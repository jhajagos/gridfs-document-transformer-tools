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
import pprint
from PIL import Image
import json


class FileChurner(object):
    def __init__(self,gridFSobj,temporary_directory,pdf_conversion_types = ["txt","tiff","png"]):
        self.gridFSobj = gridFSobj
        self.temporary_directory = temporary_directory
        self.pdf_conversion_types = pdf_conversion_types
        self.conversion_sizes = {"large" : 1000, "medium" : 750, "small" : 500, "tiny" : 250}

    def _upload_file(self,file_name,file_name_location):
        mime_type = mimetypes.guess_type(file_name)[0]
        with open(file_name_location,"rb") as f:
            self.gridFSobj.put(f, content_type = mime_type, filename = file_name)

    def process_document_to_endpoint(self,filename):
        transformation_dictionary = {"original_filename" : filename}
        converted_type =  mimetypes.guess_type(filename)[0]
        if converted_type in ['application/msword',"application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/x-mspowerpoint.12",'application/x-mspowerpoint']:
            filenames_written_1 = self.process_file(filename)
        else:
            filenames_written_1 = [filename]

        for filename_written_1 in filenames_written_1:
            if filename_written_1[-3:] == "pdf":
                transformation_dictionary["pdf_filename"] = filename_written_1
            if filename_written_1[-3:] == "txt":
                transformation_dictionary["txt_filename"] = filename_written_1

            if "pdf_filename" in transformation_dictionary:
                filenames_written_2 = self.process_file(transformation_dictionary["pdf_filename"])
                for filename_written_2 in filenames_written_2:
                    if filename_written_2[-3:] == "png":
                        if "png_originals" in transformation_dictionary:
                            transformation_dictionary["png_originals"].append(filename_written_2)
                        else:
                            transformation_dictionary["png_originals"] = [filename_written_2]
                    if "png_originals" in transformation_dictionary:
                        transformation_dictionary["png_originals"].sort()
                    if filename_written_2[-4:] == "tiff":
                        if "tiff_originals" in transformation_dictionary:
                            transformation_dictionary["tiff_originals"].append(filename_written_2)
                        else:
                            transformation_dictionary["tiff_originals"] = [filename_written_2]
                    if "tiff_originals" in transformation_dictionary:
                        transformation_dictionary["tiff_originals"].sort()

                    if filename_written_2[:-3] == "txt":
                        if "pdf_texts" in transformation_dictionary:
                            transformation_dictionary["pdf_texts"] = filename_written_2
                        else:
                            if "txt_filename" not in transformation_dictionary:
                                transformation_dictionary["txt_filename"] = filename_written_2
                            transformation_dictionary["pdf_texts"] = [filename_written_2]

        i_2_str_dict = {0: "large", 1: "medium", 2 : "small", 3: "tiny"}
        if "png_originals" in transformation_dictionary:
            for filename_png_original in transformation_dictionary["png_originals"]:
                filenames_png_downsize = self.process_file(filename_png_original)
                for i in range(len(filenames_png_downsize)):
                    png_key_name = "png_" + i_2_str_dict[i]
                    if png_key_name in transformation_dictionary:
                        transformation_dictionary[png_key_name].append(filenames_png_downsize[i])
                    else:
                        transformation_dictionary[png_key_name] = [filenames_png_downsize[i]]
        writing_location = self._generate_writing_location(filename)
        json_file_name = filename + ".json"
        full_json_file_name = os.path.join(writing_location,json_file_name)
        f = open(full_json_file_name,"w")
        transformation_dictionary_json = json.dumps(transformation_dictionary)
        f.write(transformation_dictionary_json)
        f.close()
        self._upload_file(json_file_name,full_json_file_name)
        return transformation_dictionary

    def _generate_writing_location(self,filename):
        hashed_filename = hashlib.sha1(filename).hexdigest()
        writing_location = os.path.join(self.temporary_directory,hashed_filename)
        return writing_location

    def process_file(self, filename):
        files_created = []
        writing_location = self._generate_writing_location(filename)
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
            (full_pdf_file_name_written,full_text_file_name_written) = self._convert_from_doc_to_pdf_and_text(filename_to_write)
            pdf_file_name_written  = os.path.basename(full_pdf_file_name_written)
            text_file_name_written = os.path.basename(full_text_file_name_written)
            self._upload_file(pdf_file_name_written, full_pdf_file_name_written)
            self._upload_file(text_file_name_written, full_text_file_name_written)
            files_created.append(text_file_name_written)
            files_created.append(pdf_file_name_written)

        elif content_type == 'application/x-mspowerpoint.12' or content_type == 'application/x-mspowerpoint':
            file_name_written = self._convert_from_ppt_to_pdf(filename_to_write)
            os.path.basename(file_name_written)
            pdf_file_name_written = os.path.basename(file_name_written)
            self._upload_file(pdf_file_name_written,file_name_written)
            files_created.append(pdf_file_name_written)

        elif content_type == "application/pdf":
            for conversion_type in self.pdf_conversion_types:

                file_name_pairs = self._convert_pdf_to_other_format(filename_to_write, conversion_type)
                for file_name_pair in file_name_pairs:
                    converted_file_name_written = file_name_pair[0]
                    self._upload_file(converted_file_name_written, file_name_pair[1])
                    files_created.append(converted_file_name_written)

        elif content_type == "image/x-png":
            for conversion_size_name in self.conversion_sizes.keys():
                conversion_size = self.conversion_sizes[conversion_size_name]
                new_root_file_name = self._down_sample_image(filename_to_write, conversion_size, conversion_size_name)
                converted_file_name_written = os.path.basename(new_root_file_name)
                self._upload_file(converted_file_name_written,new_root_file_name)
                files_created.append(converted_file_name_written)
        return files_created


    #TODO: Cleanup and protect from COM object dysfunction
    def _convert_from_doc_to_pdf_and_text(self,file_name):
        word = win32.gencache.EnsureDispatch("Word.Application")
        word.Documents.Open(file_name)
        pdf_file_name = file_name + ".pdf"
        word.ActiveDocument.ExportAsFixedFormat(pdf_file_name,17)
        text_file_name = file_name + ".txt"
        word.ActiveDocument.SaveAs(text_file_name,FileFormat = win32.constants.wdFormatTextLineBreaks)
        word.Quit()
        return (pdf_file_name, text_file_name)

    def _convert_from_ppt_to_pdf(self, file_name):
        powerpoint = win32.gencache.EnsureDispatch("PowerPoint.Application")
        powerpoint.Visible = True
        presentation = powerpoint.Presentations.Open(file_name)
        converted_file_name = file_name + ".pdf"
        powerpoint.Presentations.Application.ActivePresentation.SaveAs(converted_file_name,32)
        powerpoint.Quit()
        return converted_file_name

    def _convert_pdf_to_other_format(self, file_name, conversion_type):
        """Can convert a PDF file to png, tiff, and text formats"""
        acrobat = win32.gencache.EnsureDispatch("AcroExch.App")
        pdf = win32.gencache.EnsureDispatch("AcroExch.PDDoc")
        pdf.Open(file_name)
        JavaScriptBridge = pdf.GetJSObject()

        if conversion_type == "png":
            conversion_format = "com.adobe.acrobat.png"
        elif conversion_type == "tiff":
            conversion_format = "com.adobe.acrobat.tiff"
        elif conversion_type == "txt":
            conversion_format = "com.adobe.acrobat.plain-text"

        converted_file_name =  file_name + "." + conversion_type
        JavaScriptBridge.saveAs(converted_file_name,conversion_format)

        base_directory_name = os.path.split(converted_file_name)[0]

        if conversion_type != "txt":
            new_converted_file_names = glob.glob(os.path.join(base_directory_name,"*." + conversion_type))
            file_result_list = []
            for new_converted_file_name in new_converted_file_names:
                file_result_list.append([self._process_acrobat_numbered_file_name(new_converted_file_name), os.path.abspath(new_converted_file_name)])
        else:
            file_result_list = [[os.path.split(converted_file_name)[1],os.path.abspath(converted_file_name)]]

        return file_result_list

    def _down_sample_image(self, image_file_name, largest_size_in_pixels,image_suffix,image_type="PNG"):
        image = Image.open(image_file_name)
        (width,height) = image.size

        if width > height:
            new_width = int(largest_size_in_pixels)
            reduction_factor = (largest_size_in_pixels * 1.0) / (width)
            new_height = int(reduction_factor * height)
        else:
            new_height = int(largest_size_in_pixels)
            reduction_factor = (largest_size_in_pixels * 1.0) / (height)
            new_width = int(reduction_factor * width)
        new_image = image.resize((new_width,new_height), Image.ANTIALIAS)
        new_image_name = image_file_name + "." + image_suffix + "." + image_type.lower()
        new_image.save(new_image_name, image_type)
        return new_image_name

    def _process_acrobat_numbered_file_name(self, file_name):
        """Convert Acrobat exported file name 'sample5.pdf_Page_3.png' to 'sample5.pdf.3.png'"""

        cleaned_file_name = os.path.basename(file_name)
        parsed_file_name = cleaned_file_name.split("_Page_")
        reformatted_file_name = parsed_file_name[0] + "." + parsed_file_name[1]

        return reformatted_file_name

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
from PIL import Image

im = Image.open("C:\\Users\\janos\\workspace\\grid-doc-transform\\src\\test\\temp\\03bad81d968a6c5d96f0380d3fcf6ddbd709824c\\journal.pone.0029797.pdf_P
age_02.png")
im = im.resize((500,850), Image.ANTIALIAS)
im.save("C:\\Users\\janos\\workspace\\grid-doc-transform\\src\\test\\temp\\03bad81d968a6c5d96f0380d3fcf6ddbd709824c\\journal.pone.0029797.pdf_Page_02.s
.1.png")
"""
