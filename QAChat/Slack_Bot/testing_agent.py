# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 Emanuel Erben
# SPDX-FileCopyrightText: 2023 Felix Nützel

import tkinter as tk
from base_agent import BaseAgent

'''
    This is just an easy Testing Bot for testing reasons and should not be part of the final release. 
    Its purpose is to send and receive answers from our system, without having a functioning SlackBot or other.
'''


class TestingAgent(BaseAgent):
    def __init__(self, master):
        super().__init__()
        self.master = master
        master.title("My GUI")

        self.label = tk.Label(master, text="Enter some text:")
        self.label.pack()

        self.entry = tk.Entry(master)
        self.entry.pack()

        self.button = tk.Button(master, text="Submit", command=self.receive_question)
        self.button.pack()

        self.result_label = tk.Label(master, text="")
        self.result_label.pack()

    def receive_question(self, question=None, user_id=None):
        input_text = self.entry.get()
        self.api_interface.listen_for_requests(input_text, self, user_id)

    def receive_answer(self, answer, user_id=None):
        self.result_label.config(text=answer)


if __name__ == '__main__':
    root = tk.Tk()
    gui = TestingAgent(root)
    root.mainloop()
