"""
The naming convention of files starting with the original
    'Much Ado About Nothing by Shakespeare.docx'
    'Much Ado About Nothing by Shakespeare.docx.txt'
    'Much Ado About Nothing by Shakespeare.docx.pdf'
    'Much Ado About Nothing by Shakespeare.docx.pdf.1.png'
    'Much Ado About Nothing by Shakespeare.docx.pdf.2.png'
"""

import pymongo
import gridfs
import win32com.client as win32
import mimetypes
import os
import hashlib
import glob


class FileChurner(object):
    def __init__(self,gridFSobj,temporary_directory):
        self.gridFSobj = gridFSobj
        self.temporary_directory = temporary_directory

    def process_file(self, filename):
        hashed_filename = hashlib.sha1(filename).hexdigest()
        writing_location = os.path.join(self.temporary_directory,hashed_filename)
        if os.path.exists(writing_location):
            success = self._clean_and_remove_directory(writing_location)
        else:
            success = 1

        if success:
            os.mkdir(writing_location)

        grid_out = self.gridFSobj.get_last_version(filename)
        filename_to_write = os.path.join(writing_location,filename)
        file_to_write = open(filename_to_write,'wb')

        for chunk in grid_out:
            file_to_write.write(chunk)
        file_to_write.close()

        content_type = grid_out.content_type

        if content_type == 'application/msword' or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            self._convert_to_pdf_and_text_file(filename_to_write)

    def _convert_to_pdf_and_text_file(self,file_name):
        word = win32.gencache.EnsureDispatch("Word.Application")
        word.Documents.Open(file_name)
        pdf_file_name = file_name + ".pdf"
        word.ActiveDocument.ExportAsFixedFormat(pdf_file_name,17)
        text_file_name = file_name + ".txt"
        word.ActiveDocument.SaveAs(text_file_name,FileFormat = win32.constants.wdFormatTextLineBreaks)
        word.Quit()



    def process_all_files(self):
        file_names = self.gridFSobj.list()
        for filename in file_names:
            self.process_file(filename)

    def _clean_and_remove_directory(self, directory_name):
        files_to_delete = glob.glob(os.path.join(directory_name,"*"))
        for file_to_delete in files_to_delete:
            os.remove(file_to_delete)

        try:
            os.rmdir(directory_name)
            return 1
        except WindowsError:
            return 0




    """
Example in iPython opening a doc file and saving it as a pdf file.

For Office 2007 you must have the following library installed to save a file in a fixed format like XPS or PDF

http://www.microsoft.com/download/en/details.aspx?id=7

In [55]: import win32com.client as win32
In [56]: word = win32.gencache.EnsureDispatch("Word.Application")
In [57]: doc = word.Documents.Open("C:\\users\\janos\\workspace\\grid-doc-transform\\src\\test\\Much Ado About Nothing by Shakespeare.docx")
In [58]: word.ActiveDocument.ExportAsFixedFormat("C:\\users\\janos\\Desktop\\sample2.pdf",17)
In [59]: word.ActiveDocument.SaveAs("C:\\users\\janos\\Desktop\\sample2.txt",FileFormat = win32com.client.constants.wdFormatTextLineBreaks)
In [60]: word.Quit()
"""

"""
Powerpoint:
In [1]: import win32com.client as win32
In [2]: powerpoint = win32.gencache.EnsureDispatch("PowerPoint.Application")
In [3]: powerpoint.Visible = True
In [4]: presentation = powerpoint.Presentations.Open("C:\\users\\janos\\workspace\\grid-doc-transform\\src\\test\\Sample Presentation Plain Background.pptx")
In [5]: powerpoint.Presentations.Application.ActivePresentation.SaveAs("C:\\users\\janos\\Desktop\\sample5.pdf",32)

"""

"""
We need to edit the following file:

C:\Python27\Lib\site-packages\win32com\client\dynamic.py

ERRORS_BAD_CONTEXT = [
	winerror.DISP_E_MEMBERNOTFOUND,
	winerror.DISP_E_BADPARAMCOUNT,
	winerror.DISP_E_PARAMNOTOPTIONAL,
	winerror.DISP_E_TYPEMISMATCH,
	winerror.E_INVALIDARG,
        winerror.E_NOTIMPL
]

Adding the winerror.E_NOTIMPL

In [1]: import win32com.client as win32
In [4]: acrobat = win32.gencache.EnsureDispatch("AcroExch.App")
In [5]: pdf = win32.gencache.EnsureDispatch("AcroExch.PDDoc")
In [6]: pdf.Open("C:\\users\\janos\\workspace\\grid-doc-transform\\src\\test\\sample-pdf-document-with-ocr.pdf")
In [8]: j=pdf.GetJSObject()
In [9]: j.numPages
Out[9]: 3.0
In [10]: j.saveAs("C:\\users\\janos\\Desktop\\testpdf\\test.tif","com.adobe.acrobat.tiff")

"""

"""
Create a temporary directory based on a sha1 hexdigest

import sha
In [69]: s = sha.new("ddd")
In [70]: os.path.join("C:\\temp\\",s.hexdigest())
Out[70]: 'C:\\temp\\9c969ddf454079e3d439973bbab63ea6233e4087'
"""