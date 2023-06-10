from QAChat.Data_Processing.deepL_translator import DeepLTranslator
from langchain.text_splitter import NLTKTextSplitter
import nltk

CHUNK_SIZE = 200
CHUNK_OVERLAP = 50


def transform_text_to_chunks(data_information_list):
    """
    Splits the data information needed for our vector database into chunks.

    :param data_information_list: a list of data_information objects with attributes id, typ, last_changed and text
    :return: a new data_information_list in which the data was split into chunks with a specific size and overlap
    """

    new_data_information_list = []

    for data_information in data_information_list:
        # translate text
        translator = DeepLTranslator()
        data_information.text = (
            translator.translate_to(data_information.text, "EN-US")
            .text.replace("<name>", "")
            .replace("</name>", "")
        )

        # split the text
        nltk.download("punkt")
        text_splitter = NLTKTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        print(data_information.text)
        chunks = text_splitter.split_text(data_information.text)

        for index, chunk in enumerate(chunks):
            new_data_information = data_information
            new_data_information.text = chunk
            new_data_information.id = data_information.id + "_" + str(index)
            new_data_information_list.append(data_information)

    return new_data_information_list
