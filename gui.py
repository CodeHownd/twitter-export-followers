import tkinter as tk
from tkinter import simpledialog, messagebox
import tweepy
import sqlite3
import datetime

class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        container = tk.Frame(self)
        container.grid(row=0, column=0)

        self.frames = {}
        for F in (Login, Followers):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Login")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        for frame in self.frames.values():
            frame.grid_remove()
        frame = self.frames[page_name]
        frame.grid()


class Login(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.frm = tk.Frame(self)
        self.consumer_key_lbl = tk.Label(self.frm, text='Consumer Key:')
        self.consumer_key_entry = tk.Entry(self.frm, width=50)
        self.consumer_secret_lbl = tk.Label(self.frm, text='Consumer Secret:')
        self.consumer_secret_entry = tk.Entry(self.frm, width=50)
        self.access_token_lbl = tk.Label(self.frm, text='Access Token')
        self.access_token_entry = tk.Entry(self.frm, width=50)
        self.access_token_secret_lbl = tk.Label(self.frm, text='Access Secret')
        self.access_token_secret_entry = tk.Entry(self.frm, width=50)

        self.login_btn = tk.Button(self, text='Log in', command=self.try_login, height=3, width=20)

        self.frm.grid(row=0, column=0, pady=20, padx=20)
        self.consumer_key_lbl.grid(row=0, column=0)
        self.consumer_key_entry.grid(row=0, column=1)
        self.consumer_secret_lbl.grid(row=1, column=0)
        self.consumer_secret_entry.grid(row=1, column=1)
        self.access_token_lbl.grid(row=2, column=0)
        self.access_token_entry.grid(row=2, column=1)
        self.access_token_secret_lbl.grid(row=3, column=0)
        self.access_token_secret_entry.grid(row=3, column=1)

        self.login_btn.grid(row=1, column=0, pady=2)

    def try_login(self):
        consumer_key = self.consumer_key_entry.get()
        consumer_secret = self.consumer_secret_entry.get()
        access_token = self.access_token_entry.get()
        access_token_secret = self.access_token_secret_entry.get()
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        global api
        api = tweepy.API(auth)
        if api:
            self.get_followers(api)
            self.controller.show_frame('Followers')

    def create_table(self):
        conn = sqlite3.connect('followers.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS followers
        (id integer NOT NULL PRIMARY KEY, handle text, bio text,
              followers integer, verified integer, location text, date_retrieved text, DMd_already integer)''')
        conn.commit()
        conn.close()

    def get_followers(self, api):
        self.create_table()
        followers_json = api.followers()
        for follower in followers_json:
            user_id = follower._json['id']
            handle = follower._json['screen_name']
            bio = follower._json['description']
            followers_count = follower._json['followers_count']
            verified = follower._json['verified']
            location = follower._json['location']
            conn = sqlite3.connect('followers.db')
            c = conn.cursor()
            c.execute("REPLACE INTO followers VALUES (?,?,?,?,?,?,?,?)", (user_id, handle, bio,
                                                                         followers_count, verified, location,
                                                                         datetime.datetime.now(), 0))
            conn.commit()
            conn.close()


class Followers(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.query = ''
        self.controller = controller
        self.filters = tk.Frame(self)

        self.var = tk.IntVar()
        self.pre_checkbox_query = ''

        self.get_followers_btn = tk.Button(self.filters, text='Preview Followers', command=lambda: self.preview_followers(self.query))
        self.sort_by_count_btn = tk.Button(self.filters, text='Sort by Most Followed', command=self.sort_by_count)
        self.sort_by_verified_btn = tk.Button(self.filters, text='Sort by Verified', command=self.sort_by_verified)
        self.sort_by_bio_entry = tk.Entry(self.filters, width=15)
        self.sort_by_bio_btn = tk.Button(self.filters, text='Filter by Bio', command=self.sort_by_bio)
        self.dm_already = tk.Checkbutton(self.filters, text="hide already DM'd", variable=self.var, command=self.sort_by_dmd)
        self.send_test_DM = tk.Button(self.filters, text='send_test_DMs', command=self.send_test_DMs)
        self.send_full_DM = tk.Button(self.filters, text='send_full_DMs', command=self.send_full_DMs)
        self.filters.pack(anchor='nw', padx=5, pady=10)

        self.get_followers_btn.grid(row=0, column=0)
        self.sort_by_count_btn.grid(row=0, column=1)
        self.sort_by_verified_btn.grid(row=0, column=2)
        self.sort_by_bio_entry.grid(row=0, column=3)
        self.sort_by_bio_btn.grid(row=0, column=4)
        self.dm_already.grid(row=0, column=5)
        self.send_test_DM.grid(row=0, column=6)
        self.send_full_DM.grid(row=0, column=7)

        self.follower_row = tk.Frame(self)
        self.follower_row.pack(anchor='nw')


    def preview_followers(self, query):

        for child in self.follower_row.winfo_children():
            child.destroy()

        conn = sqlite3.connect('followers.db')
        c = conn.cursor()
        if len(query) == 0:
            query = 'SELECT * FROM followers LIMIT 15'
        if self.var.get() == 1:
            query = self.query.replace('*', 'id')
            query = f'SELECT * FROM followers WHERE id IN ({query}) AND DMd_already = 0' if 'id' in query else query
            self.pre_checkbox_query = self.query

        count = self.create_headers()
        for row in c.execute(query):

            follower_id = tk.Label(self.follower_row, text=row[0])
            username = tk.Label(self.follower_row, text=row[1])
            desc = tk.Label(self.follower_row, text=row[2])
            follower_count = tk.Label(self.follower_row, text=row[3])
            is_verified = tk.Label(self.follower_row, text="yes" if row[4] == 1 else "no")
            location = tk.Label(self.follower_row, text=row[5])
            is_dmd = tk.Label(self.follower_row, text=row[7])

            follower_id.grid(row=count, column=0, sticky='w')
            username.grid(row=count, column=1, sticky='w')
            desc.grid(row=count, column=2, sticky='w')
            follower_count.grid(row=count, column=3, sticky='w')
            is_verified.grid(row=count, column=4, sticky='w')
            location.grid(row=count, column=5, sticky='w')
            is_dmd.grid(row=count, column=6, sticky='w')
            count += 1
        self.query = query

    def create_headers(self):
        id_header = tk.Label(self.follower_row, text="user id")
        handle_header = tk.Label(self.follower_row, text="handle")
        bio_header = tk.Label(self.follower_row, text=f'bio')
        follower_count_header = tk.Label(self.follower_row, text='follower count')
        is_verified_header = tk.Label(self.follower_row, text='verified?')
        location_header = tk.Label(self.follower_row, text='location')
        dmd_already = tk.Label(self.follower_row, text='DM\'d Already?')
        id_header.grid(row=0, column=0, sticky='w')
        handle_header.grid(row=0, column=1, sticky='w')
        bio_header.grid(row=0, column=2, sticky='w')
        follower_count_header.grid(row=0, column=3, sticky='w')
        is_verified_header.grid(row=0, column=4, sticky='w')
        location_header.grid(row=0, column=5, sticky='w')
        dmd_already.grid(row=0, column=6, sticky='w')
        count = 1
        return count

    def sort_by_verified(self):
        query = 'SELECT * FROM followers ORDER BY verified DESC LIMIT 15'
        self.preview_followers(query)

    def sort_by_count(self):
        query = 'SELECT * FROM followers ORDER BY followers DESC LIMIT 15'
        self.preview_followers(query)

    def sort_by_bio(self):
        filter_value = self.sort_by_bio_entry.get()
        self.sort_by_bio_entry.delete(0, tk.END)
        query = f'SELECT * FROM followers WHERE bio LIKE \'%{filter_value}%\' LIMIT 15'
        self.preview_followers(query)

    def sort_by_dmd(self):
        if self.var.get() == 1:
            query = self.query.replace('*', 'id')
            query = f'SELECT * FROM followers WHERE id IN ({query}) AND DMd_already = 0' if 'id' in query else query
            self.pre_checkbox_query = self.query
            self.preview_followers(query)
        elif self.var.get() == 0:
            query = self.pre_checkbox_query
            self.preview_followers(query)

    def send_test_DMs(self):
        message = simpledialog.askstring("Input", "Message to send followers", parent=self.controller)
        conn = sqlite3.connect('followers.db')
        c = conn.cursor()
        handles = []
        for row in c.execute(self.query).fetchall():
            api.send_direct_message(row[0], message)
            with conn:
                conn.execute('UPDATE followers SET DMd_already = 1 WHERE id = (?)', (row[0],))
                conn.commit()
            handles.append(row[1])
        handles = '\n'.join(handles)
        messagebox.showinfo("Information", f'''Sent message: "{message}" to:
        {handles}''')

    def send_full_DMs(self):
         pass

app = App()
app.mainloop()
