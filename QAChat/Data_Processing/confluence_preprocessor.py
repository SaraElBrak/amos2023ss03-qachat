# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 Hafidz Arifin
# SPDX-FileCopyrightText: 2023 Abdelkader Alkadour


from atlassian import Confluence
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import os, io, requests, PyPDF2, supabase


load_dotenv("../tokens.env")

CONFLUENCE_ADRESS = os.getenv("CONFLUENCE_ADRESS")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_PASSWORD = os.getenv("CONFLUENCE_PASSWORD")

SUPABASE_URL =  os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY =  os.getenv("SUPABASE_SERVICE_KEY")


class ConfluencePreprocessor():
    spaces = []
    pages = []
    restricted_spaces = []
    restricted_pages = []
    
    confluence = Confluence( 
                    url=CONFLUENCE_ADRESS,
                    username=CONFLUENCE_USERNAME,
                    password=CONFLUENCE_PASSWORD,
                    cloud=True)

    supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


    def init_blacklist(self):
        blacklist = self.supabase_client.table("confluence_blacklist").select("*").execute().data
 
        for i in blacklist:
            if "/pages/" in i['identifer']:
                self.restricted_pages.append(i['identifer'].split('/')[7])
            else:
                self.restricted_spaces.append(i['identifer'].split('/')[5])


    def get_spaces(self):
        start = 0
        limit = 500
        spaces = []

        #get all spaces starting from 0 to 500 (max of possible retrieved spaces via API)
        #while no empty response, keep request
        while True:
            new_spaces = self.confluence.get_all_spaces(start=start, limit=limit, expand=None)
            if new_spaces['size'] ==  0:
                break
            spaces.extend(new_spaces['results'])
            start += limit

        # exclude personal/user spaces only global spaces and save necessary data
        for space in spaces:
            if space['type'] == 'global':
                if space['key'] not in self.restricted_spaces:
                    self.spaces.append({'key': space['key'],
                                        'name': space['name']}) 


    def get_page_by_id(self, id): 
        return self.get_text_from_html(self.confluence.get_page_by_id(id,
                                              expand='body.storage')['body']['storage']['value'])
    

    def get_comments(self, id):
        comments = []
        for i in self.confluence.get_page_child_by_type(id, 
                                                        type='comment', 
                                                        start=None, 
                                                        limit=None, 
                                                        expand='body.storage'): #TODO
            comments.append(self.get_text_from_html(i['body']['storage']['value']))
        return comments   


    def get_page_attacments(self, id):
        attachments_container = self.confluence.get_attachments_from_content(page_id=id, start=0, limit=500)
        attachments = attachments_container['results']
        pdf_content = []
        for attachment in attachments:
                content = ""
                fname = attachment['title']
                download_link = self.confluence.url + attachment['_links']['download']
                r = requests.get(download_link, auth=(self.confluence.username, self.confluence.password))
                if r.status_code == 200:
                 #   with open(fname, "wb") as f:
                 #       for bits in r.iter_content():
                 #           f.write(bits)
                    pdf_file = io.BytesIO(r.content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)

                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        content += text
                    pdf_content.append(content)
        return pdf_content 
    

    def get_text_from_html(self, html):
        return BeautifulSoup(html, features="html.parser").get_text().replace('\n', ' ')


    def get_pages_from_space(self, key, name):
        start = 0
        limit = 500
        pages = []

        #get all pages from a space starting from 0 to 500 (max of possible retrieved pages via API)
        #while no empty response, keep request
        while True:
            new_pages = self.confluence.get_all_pages_from_space(key, 
                                                                 start=start, 
                                                                 limit=limit, 
                                                                 status=None, 
                                                                 expand=None, 
                                                                 content_type='page')
            pages.extend(new_pages)
            if len(new_pages) <  limit:
                break
            start += limit

        for page in pages: 
            if page['id'] not in self.restricted_pages:
                self.pages.append({'space': name, 
                                   'title': page['title'], 
                                   'content': self.get_page_by_id(page['id']),
                                   'attachments': self.get_page_attacments(page['id']),
                                   'comments': self.get_comments(page['id'])})


    def get_pages(self):
        self.init_blacklist()
        self.get_spaces()
        for space in self.spaces:
            self.get_pages_from_space(space['key'], space['name'])


    def update_data(self):
        self.get_pages()
        for page in self.pages:
            self.supabase_client.table('confluence_data').insert({
                "space": page["space"],
                "title": page["title"],
                "content": page["content"],
                "attachments": page["attachments"],
                "comments": page["comments"]
        }).execute()



if __name__ == "__main__":
    data_preprocessor = ConfluencePreprocessor()
    data_preprocessor.update_data()
   
