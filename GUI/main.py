import tkinter as tk
import customtkinter as ctk
import shutil
import os
import datetime
import requests
import webbrowser

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def open_pdf(event,pdf_url):
    webbrowser.open_new(pdf_url)

class LaxDocHomeUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LaxDoc Home")
        self.root.geometry("800x600")

        # Menubar frame
        self.menu_frame = ctk.CTkFrame(self.root, width=200)
        self.menu_frame.pack(side='left', fill='y')

        # Menu buttons
        buttons = [
            ("Import Template", self.show_import_template),
            ("Export Template", self.show_export_template),
            ("Delete Template", self.show_delete_template),
            ("Generate Document", self.show_generate_document),
            ("Search Document", self.show_search_document)
        ]
        for text, command in buttons:
            ctk.CTkButton(self.menu_frame, text=text, command=command).pack(pady=10, padx=10, fill='x')

        # Appearance dropdown
        self.appearance_label = ctk.CTkLabel(self.menu_frame, text="Choose Appearance:", font=('Arial', 14))
        self.appearance_label.pack(pady=10)
        self.appearance_var = tk.StringVar(value="System")
        self.appearance_dropdown = ctk.CTkOptionMenu(self.menu_frame,
                                                     variable=self.appearance_var,
                                                     values=["System", "Dark", "Light"],
                                                     command=self.change_appearance)
        self.appearance_dropdown.pack(pady=5)

        # Main content frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(side='right', fill='both', expand=True)

        # Default view
        self.show_import_template()

    def change_appearance(self, mode):
        ctk.set_appearance_mode(mode)

    def show_import_template(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Import Template", font=('Arial', 18)).pack(pady=20)
        ctk.CTkButton(self.main_frame, text="Select Template File", command=self.import_template).pack(pady=5)

    def import_template(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("LaTeX Files", "*.tex")])
        print(file_path)
        if file_path:
            template_name = os.path.basename(file_path)
            template_type = "general"
            with open(file_path, 'rb') as file:
                files = {'template': file}
                data = {
                    'action': 'importTemplate',
                    'name': template_name,
                    'path': file_path,  # Ensure this is not empty
                    'type': template_type
                }
                response = requests.post('http://localhost:8000/api.php', data=data, files=files)

                print("Response status code:", response.status_code)
                print("Response text:", response.text)  # Print response content before parsing

                try:
                    json_response = response.json()
                    print("JSON Response:", json_response)
                    if json_response.get('success'):
                        self.show_toast_message(f"Template '{template_name}' imported successfully")
                    else:
                        self.show_toast_message("Failed to import template")
                except requests.exceptions.JSONDecodeError:
                    print("Error: Response is not valid JSON")
                    self.show_toast_message("Server returned an invalid response")




    def show_export_template(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Export Template", font=('Arial', 18, 'bold')).pack(pady=20)
        templates = self.get_template_list()
        if not templates:
            ctk.CTkLabel(self.main_frame, text="No templates available").pack()
            return
        self.export_template_var = ctk.StringVar()
        ctk.CTkComboBox(self.main_frame, variable=self.export_template_var, values=templates, state='readonly').pack(pady=10, padx=20, fill='x')
        ctk.CTkButton(self.main_frame, text="Export Selected Template", command=self.export_template, fg_color="#2AA876", hover_color="#207A5E").pack(pady=15)

    def export_template(self):
        template_name = self.export_template_var.get()
        if not template_name:
            self.show_toast_message("Please select a template to export")
            return
        dest_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX Files", "*.tex")],
            initialfile=template_name)
        if dest_path:
            response = requests.get(f'http://localhost:8000/api.php?action=exportTemplate&name={template_name}')
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
                self.show_toast_message(f"Template exported to:\n{dest_path}")
            else:
                self.show_toast_message("Failed to export template")


    def show_delete_template(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Delete Template", font=('Arial', 18, 'bold')).pack(pady=20)
        templates = self.get_template_list()
        if not templates:
            ctk.CTkLabel(self.main_frame, text="No templates available").pack()
            return
        self.delete_template_var = ctk.StringVar()
        frame = ctk.CTkScrollableFrame(self.main_frame, height=200)
        frame.pack(pady=10, fill='both', expand=True)
        for template in templates:
            ctk.CTkRadioButton(frame, text=template, variable=self.delete_template_var, value=template).pack(anchor='w', pady=2)
        ctk.CTkButton(self.main_frame, text="Delete Selected Template", command=self.confirm_delete, fg_color="#B33A3A", hover_color="#8C2B2B").pack(pady=15)

    def confirm_delete(self):
        template = self.delete_template_var.get()
        if not template:
            self.show_toast_message("Please select a template to delete")
            return
        if tk.messagebox.askyesno("Confirm Delete", f"Delete template '{template}' permanently?"):
            response = requests.post('http://localhost:8000/api.php', 
                data={'action': 'deleteTemplate', 'name': template})
            if response.json()['success']:
                self.show_toast_message(f"Template '{template}' deleted successfully")
                self.show_delete_template()  # Refresh view
            else:
                self.show_toast_message("Failed to delete template")

    def show_generate_document(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Generate Document", font=('Arial', 18)).pack(pady=20)
        self.template_var = ctk.StringVar()
        ctk.CTkComboBox(self.main_frame, variable=self.template_var, values=self.get_template_list()).pack(pady=5)
        self.date_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Date")
        self.place_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Place")
        self.content_text = ctk.CTkTextbox(self.main_frame, height=150)
        for widget in [self.date_entry, self.place_entry, self.content_text]:
            widget.pack(pady=5, padx=20, fill='x')
        ctk.CTkButton(self.main_frame, text="Generate", command=self.prepare_generation).pack(pady=10)

    def prepare_generation(self):
        template_name = self.template_var.get()
        #file_path = f'templates/{template_name}'  # Adjust this path
        file_path = os.path.abspath(f'templates/{template_name}')

        if not os.path.exists(file_path):
            self.show_toast_message("Template file not found"+file_path)
            return

        doc_data = {
            'action': 'generateDocument',
            'template': template_name,
            'date': self.date_entry.get(),
            'place': self.place_entry.get(),
            'content': self.content_text.get("1.0", tk.END).strip(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        with open(file_path, 'rb') as file:
            files = {'templateFile': file}
            response = requests.post('http://localhost:8000/api.php', data=doc_data, files=files)

        if response.status_code == 200:
            json_response = response.json()
            print("JSON Response:", json_response)  # Debugging
            if json_response.get('success'):
                document_id = json_response['documentId']
                pdf_url = json_response.get('pdf_url', '')
                self.show_toast_message(f"Document generated with ID: {document_id}\nPDF: {pdf_url}")
                labellink = ctk.CTkLabel(self.main_frame, text=f"{pdf_url}", fg_color="green", cursor="hand2")
                labellink.pack(pady=10)

                labellink.bind("<Button-1>", lambda event: open_pdf(event, pdf_url))
            else:
                self.show_toast_message("Failed to generate document: " + json_response.get('error', 'Unknown error'))
        else:
            self.show_toast_message("Server error: " + response.text)
        



    def show_search_document(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Search Document", font=('Arial', 18)).pack(pady=20)

        self.search_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Search by keyword...")
        self.search_entry.pack(pady=5, padx=20, fill='x')

        self.date_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Search by date (YYYY-MM-DD)")
        self.date_entry.pack(pady=5, padx=20, fill='x')

        self.place_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Search by place")
        self.place_entry.pack(pady=5, padx=20, fill='x')

        ctk.CTkButton(self.main_frame, text="Search", command=self.perform_search).pack(pady=5)


    def perform_search(self):
        query = self.search_entry.get()
        date = self.date_entry.get() if hasattr(self, 'date_entry') else ''
        place = self.place_entry.get() if hasattr(self, 'place_entry') else ''

        results = self.search_documents(query, date, place)
        self.display_search_results(results)

    def display_search_results(self, results):
        self.clear_main_frame()
        
        ctk.CTkLabel(self.main_frame, text="Search Results", font=('Arial', 18)).pack(pady=10)
        
        if not results:
            ctk.CTkLabel(self.main_frame, text="No documents found.").pack()
            return
        
        frame = ctk.CTkScrollableFrame(self.main_frame, height=300)
        frame.pack(pady=10, fill='both', expand=True)
        
        for res in results:
            doc_text = f"{res['documentId']} - {res['template']} ({res['date']}, {res['place']})"
            doc_label = ctk.CTkLabel(frame, text=doc_text, justify='left')
            doc_label.pack(anchor='w', padx=10, pady=2)
            
            regenerate_button = ctk.CTkButton(frame, text="Regenerate", 
                                            command=lambda doc=res: self.regenerate_document(doc))
            regenerate_button.pack(anchor='e', padx=10, pady=2)

    def regenerate_document(self, document):
        document_id = document['documentId']
        
        # Send request to regenerate the document
        data = {
            'action': 'regenerateDocument',
            'documentId': document_id
        }

        response = requests.post('http://localhost:8000/api.php', data=data)

        if response.status_code == 200:
            print("Response text:", response.text)
            json_response = response.json()
            if json_response.get('success'):
                pdf_url = json_response.get('pdf_url', '')
                self.show_toast_message(f"Document regenerated successfully!\nPDF: {pdf_url}")

                # Add clickable link to open PDF
                labellink = ctk.CTkLabel(self.main_frame, text="Open Regenerated PDF", fg_color="green", cursor="hand2")
                labellink.pack(pady=10)
                labellink.bind("<Button-1>", lambda event: open_pdf(event, pdf_url))
            else:
                self.show_toast_message(f"Failed to regenerate: {json_response.get('error', 'Unknown error')}")
        else:
            self.show_toast_message("Server error: " + response.text)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def get_template_list(self):
        response = requests.get('http://localhost:8000/api.php?action=getTemplates')
        if response.status_code == 200:
            return response.json()
        else:
            self.show_toast_message("Failed to fetch template list")
            return []
    def show_toast_message(self, message):
        # Destroy existing toast if present
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == message:
                widget.destroy()
        
        toast = ctk.CTkLabel(
            self.main_frame,
            text=message,
            corner_radius=10,
            fg_color=("gray75", "gray25"),
            text_color=("gray10", "gray90")
        )
        toast.pack(pady=10, padx=10, side='bottom')
        toast.after(3000, toast.destroy)
    def search_documents(self, query, date='', place=''):
        data = {
            'action': 'searchDocuments',
            'query': query,
            'date': date,
            'place': place
        }
        response = requests.post('http://localhost:8000/api.php', data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.show_toast_message("Failed to search documents")
            return []


if __name__ == "__main__":
    root = ctk.CTk()
    app = LaxDocHomeUI(root)
    root.mainloop()
