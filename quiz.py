import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import json
import os
import time
from datetime import datetime

DATA_FILE = "questions.json"
USERS_FILE = "users.json"
RESULTS_FILE = "results.txt"
TIME_PER_QUESTION = 20

def ensure_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "Software Engineering": [
                    {"question":"Which model is also known as the linear sequential model?","options":["Waterfall Model","Spiral Model","RAD Model","Prototype Model"],"answer":0},
                    {"question":"Requirement gathering is done in which phase?","options":["Design","Analysis","Testing","Deployment"],"answer":1},
                    {"question":"White-box testing is also called?","options":["Behavioral Testing","Structural Testing","User Testing","Black-box Testing"],"answer":1}
                ]
            }, f, indent=2)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({"admin":"admin"}, f, indent=2)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(u):
    with open(USERS_FILE, "w") as f:
        json.dump(u, f, indent=2)

def save_result(username, category, score, total):
    with open(RESULTS_FILE, "a") as f:
        f.write(f"{datetime.now()} | {username} | {category} | {score}/{total}\n")

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz System")
        self.data = {}
        self.users = {}
        self.current_user = None
        self.current_category = None
        self.questions = []
        self.q_index = 0
        self.score = 0
        self.time_left = TIME_PER_QUESTION
        self.selected_option = tk.IntVar()
        self.frames = {}
        self.build_ui()
        self.load_all()

    def load_all(self):
        self.data = load_data()
        self.users = load_users()
        self.refresh_category_list()

    def build_ui(self):
        for f in ("login","menu","quiz","admin"):
            frame = tk.Frame(self.root)
            frame.grid(row=0,column=0,sticky="nsew")
            self.frames[f]=frame
        self.build_login()
        self.build_menu()
        self.build_quiz()
        self.build_admin()
        self.show_frame("login")

    def show_frame(self,name):
        frame=self.frames[name]
        frame.tkraise()

    def build_login(self):
        f=self.frames["login"]
        tk.Label(f,text="Username").pack(pady=5)
        self.login_user=tk.Entry(f)
        self.login_user.pack(pady=5)
        tk.Label(f,text="Password").pack(pady=5)
        self.login_pass=tk.Entry(f,show="*")
        self.login_pass.pack(pady=5)
        tk.Button(f,text="Login",command=self.handle_login).pack(pady=5)
        tk.Button(f,text="Register",command=self.handle_register).pack(pady=5)
        tk.Button(f,text="Quit",command=self.root.quit).pack(pady=5)

    def handle_register(self):
        u=self.login_user.get().strip()
        p=self.login_pass.get().strip()
        if not u or not p:
            messagebox.showerror("Error","Enter username and password")
            return
        if u in self.users:
            messagebox.showerror("Error","User exists")
            return
        self.users[u]=p
        save_users(self.users)
        messagebox.showinfo("OK","Registered")

    def handle_login(self):
        u=self.login_user.get().strip()
        p=self.login_pass.get().strip()
        if u in self.users and self.users[u]==p:
            self.current_user=u
            if u=="admin":
                self.show_frame("admin")
            else:
                self.show_frame("menu")
            self.login_user.delete(0,tk.END)
            self.login_pass.delete(0,tk.END)
        else:
            messagebox.showerror("Error","Invalid credentials")

    def build_menu(self):
        f=self.frames["menu"]
        tk.Label(f,text="Select Category").pack(pady=5)
        self.cat_listbox=tk.Listbox(f,height=10)
        self.cat_listbox.pack(pady=5)
        tk.Button(f,text="Start Quiz",command=self.start_quiz_from_menu).pack(pady=5)
        tk.Button(f,text="Logout",command=self.logout_to_login).pack(pady=5)
        tk.Button(f,text="Admin Panel (if admin)",command=lambda: self.show_frame("admin")).pack(pady=5)

    def refresh_category_list(self):
        clb = getattr(self, "cat_listbox", None)
        if clb:
            clb.delete(0,tk.END)
            for c in sorted(self.data.keys()):
                clb.insert(tk.END,c)
        admin_cat = getattr(self, "admin_cat_listbox", None)
        if admin_cat:
            admin_cat.delete(0,tk.END)
            for c in sorted(self.data.keys()):
                admin_cat.insert(tk.END,c)

    def start_quiz_from_menu(self):
        sel = self.cat_listbox.curselection()
        if not sel:
            messagebox.showerror("Error","Select a category")
            return
        cat = self.cat_listbox.get(sel[0])
        self.start_quiz(cat)

    def build_quiz(self):
        f=self.frames["quiz"]
        self.q_label=tk.Label(f,text="",wraplength=500,justify="left",font=("Arial",12))
        self.q_label.pack(pady=10)
        self.opt_vars=[]
        for i in range(4):
            rb = tk.Radiobutton(f,variable=self.selected_option,value=i,text="",anchor="w",justify="left",wraplength=500)
            rb.pack(fill="x",padx=20,pady=2)
            self.opt_vars.append(rb)
        self.timer_label=tk.Label(f,text="")
        self.timer_label.pack(pady=5)
        btn_frame = tk.Frame(f)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame,text="Submit",command=self.submit_answer).grid(row=0,column=0,padx=5)
        tk.Button(btn_frame,text="Next",command=self.next_question).grid(row=0,column=1,padx=5)
        tk.Button(btn_frame,text="Quit",command=self.end_quiz).grid(row=0,column=2,padx=5)

    def start_quiz(self,category):
        self.current_category=category
        self.questions=list(self.data.get(category,[]))
        if not self.questions:
            messagebox.showerror("Error","No questions in this category")
            return
        import random
        random.shuffle(self.questions)
        self.q_index=0
        self.score=0
        self.show_frame("quiz")
        self.load_question()

    def load_question(self):
        if self.q_index>=len(self.questions):
            self.finish_quiz()
            return
        q=self.questions[self.q_index]
        self.q_label.config(text=f"Q{self.q_index+1}. {q['question']}")
        for i,opt in enumerate(q['options']):
            self.opt_vars[i].config(text=f"{i+1}. {opt}")
        self.selected_option.set(-1)
        self.time_left = TIME_PER_QUESTION
        self.update_timer()

    def update_timer(self):
        self.timer_label.config(text=f"Time left: {self.time_left}s")
        if self.time_left<=0:
            messagebox.showinfo("Time up","Time's up for this question")
            self.next_question()
            return
        self.time_left-=1
        self.root.after(1000,self.update_timer)

    def submit_answer(self):
        sel = self.selected_option.get()
        if sel<0 or sel>3:
            messagebox.showwarning("Warning","Select an option or press Next to skip")
            return
        q=self.questions[self.q_index]
        if sel==q['answer']:
            self.score+=1
            messagebox.showinfo("Correct","Correct answer")
        else:
            correct = q['options'][q['answer']]
            messagebox.showinfo("Wrong",f"Wrong. Correct answer: {correct}")
        self.next_question()

    def next_question(self):
        self.q_index+=1
        if self.q_index<len(self.questions):
            self.load_question()
        else:
            self.finish_quiz()

    def finish_quiz(self):
        total=len(self.questions)
        messagebox.showinfo("Quiz Finished",f"Score: {self.score}/{total}")
        save_result(self.current_user,self.current_category,self.score,total)
        self.show_frame("menu")

    def end_quiz(self):
        if messagebox.askyesno("Confirm","End quiz and return to menu?"):
            self.show_frame("menu")

    def logout_to_login(self):
        self.current_user=None
        self.show_frame("login")

    def build_admin(self):
        f=self.frames["admin"]
        top = tk.Frame(f)
        top.pack(side="left",fill="y",padx=10,pady=10)
        tk.Label(top,text="Categories").pack()
        self.admin_cat_listbox=tk.Listbox(top,height=10)
        self.admin_cat_listbox.pack()
        btnf = tk.Frame(top)
        btnf.pack(pady=5)
        tk.Button(btnf,text="Add Category",command=self.add_category).grid(row=0,column=0,padx=3)
        tk.Button(btnf,text="Delete Category",command=self.delete_category).grid(row=0,column=1,padx=3)
        mid = tk.Frame(f)
        mid.pack(side="left",fill="both",expand=True,padx=10,pady=10)
        tk.Label(mid,text="Questions").pack()
        self.admin_q_listbox=tk.Listbox(mid,height=15,width=70)
        self.admin_q_listbox.pack()
        qbtnf = tk.Frame(mid)
        qbtnf.pack(pady=5)
        tk.Button(qbtnf,text="Add Question",command=self.add_question_popup).grid(row=0,column=0,padx=3)
        tk.Button(qbtnf,text="Delete Question",command=self.delete_question).grid(row=0,column=1,padx=3)
        tk.Button(qbtnf,text="Import JSON",command=self.import_json).grid(row=0,column=2,padx=3)
        right = tk.Frame(f)
        right.pack(side="left",fill="y",padx=10,pady=10)
        tk.Button(right,text="Save & Refresh",command=self.save_and_refresh).pack(pady=3)
        tk.Button(right,text="View Results",command=self.view_results).pack(pady=3)
        tk.Button(right,text="Logout",command=self.admin_logout).pack(pady=3)
        tk.Button(right,text="Back to Menu",command=lambda:self.show_frame("menu")).pack(pady=3)
        self.admin_cat_listbox.bind("<<ListboxSelect>>",self.on_admin_cat_select)
        self.refresh_category_list()

    def add_category(self):
        name = simpledialog.askstring("New Category","Enter category name")
        if not name: return
        if name in self.data:
            messagebox.showerror("Error","Category exists")
            return
        self.data[name]=[]
        save_data(self.data)
        self.refresh_category_list()

    def delete_category(self):
        sel = self.admin_cat_listbox.curselection()
        if not sel: messagebox.showerror("Error","Select a category"); return
        name = self.admin_cat_listbox.get(sel[0])
        if messagebox.askyesno("Confirm",f"Delete category '{name}' and all its questions?"):
            del self.data[name]
            save_data(self.data)
            self.refresh_category_list()
            self.admin_q_listbox.delete(0,tk.END)

    def on_admin_cat_select(self,event):
        sel = self.admin_cat_listbox.curselection()
        if not sel: return
        name = self.admin_cat_listbox.get(sel[0])
        self.admin_q_listbox.delete(0,tk.END)
        for i,q in enumerate(self.data.get(name,[]),1):
            opts = " | ".join(q['options'])
            self.admin_q_listbox.insert(tk.END,f"{i}. {q['question']}  [{opts}]  (Ans: {q['answer']+1})")

    def add_question_popup(self):
        sel = self.admin_cat_listbox.curselection()
        if not sel: messagebox.showerror("Error","Select a category"); return
        cat = self.admin_cat_listbox.get(sel[0])
        popup = tk.Toplevel(self.root)
        popup.title("Add Question")
        tk.Label(popup,text="Question").pack()
        qentry=tk.Entry(popup,width=80)
        qentry.pack()
        opts = []
        for i in range(4):
            tk.Label(popup,text=f"Option {i+1}").pack()
            e=tk.Entry(popup,width=80)
            e.pack()
            opts.append(e)
        tk.Label(popup,text="Correct Option Number (1-4)").pack()
        ans_entry=tk.Entry(popup,width=5)
        ans_entry.pack()
        def add_q():
            qtxt = qentry.get().strip()
            olist=[o.get().strip() for o in opts]
            try:
                a = int(ans_entry.get().strip())-1
            except:
                messagebox.showerror("Error","Answer must be 1-4"); return
            if not qtxt or any(not x for x in olist) or a not in range(4):
                messagebox.showerror("Error","Fill all fields correctly"); return
            self.data.setdefault(cat,[]).append({"question":qtxt,"options":olist,"answer":a})
            save_data(self.data)
            popup.destroy()
            self.on_admin_cat_select(None)
        tk.Button(popup,text="Add",command=add_q).pack(pady=5)

    def delete_question(self):
        cat_sel = self.admin_cat_listbox.curselection()
        q_sel = self.admin_q_listbox.curselection()
        if not cat_sel or not q_sel:
            messagebox.showerror("Error","Select category and question"); return
        cat = self.admin_cat_listbox.get(cat_sel[0])
        idx = q_sel[0]
        if messagebox.askyesno("Confirm","Delete selected question?"):
            del self.data[cat][idx]
            save_data(self.data)
            self.on_admin_cat_select(None)

    def save_and_refresh(self):
        save_data(self.data)
        self.refresh_category_list()
        messagebox.showinfo("Saved","Data saved")

    def view_results(self):
        if not os.path.exists(RESULTS_FILE):
            messagebox.showinfo("Results","No results yet")
            return
        with open(RESULTS_FILE,"r") as f:
            txt = f.read()
        popup = tk.Toplevel(self.root)
        popup.title("Results")
        t = tk.Text(popup,width=80,height=30)
        t.pack()
        t.insert(tk.END,txt)

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not path: return
        try:
            with open(path,"r") as f:
                newdata = json.load(f)
            for k,v in newdata.items():
                if k in self.data:
                    self.data[k].extend(v)
                else:
                    self.data[k]=v
            save_data(self.data)
            self.refresh_category_list()
            messagebox.showinfo("Imported","Questions imported")
        except Exception as e:
            messagebox.showerror("Error",str(e))

    def admin_logout(self):
        self.current_user=None
        self.show_frame("login")

if __name__=="__main__":
    ensure_files()
    root=tk.Tk()
    root.geometry("800x600")
    app=QuizApp(root)
    root.mainloop()
