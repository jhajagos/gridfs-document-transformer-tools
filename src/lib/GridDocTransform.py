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
from PIL import Image, ImageFilter
import json
import urllib
import string
import nltk
import pyTripleSimple
import WordCloud
import NER
import sys, traceback
import codecs
import time

class FileChurner(object):
    def __init__(self,gridFSobj,temporary_directory,pdf_conversion_types = ["txt","tiff","png"]):
        self.gridFSobj = gridFSobj
        self.temporary_directory = temporary_directory
        self.pdf_conversion_types = pdf_conversion_types
        self.conversion_sizes = {"large" : 1000, "medium" : 750, "small" : 500, "tiny" : 250}
        self.discover_entities_done = False

    def _upload_file(self,file_name,file_name_location):
        mime_type = mimetypes.guess_type(file_name)[0]
        with open(file_name_location,"rb") as f:
            self.gridFSobj.put(f, content_type = mime_type, filename = file_name)

    def process_document_to_endpoint(self,filename):
        #clean up older version tranformation dictionary files
        #self.clean_transformation_dictionary(filename)
        start_time = time.time()
        pdf_done = False
        self.discover_entities_done = False
        transformation_dictionary = {"original_filename" : filename}

        try:
            converted_type =  mimetypes.guess_type(filename)[0]
            #if converted_type in ['application/msword']:
            if converted_type in ['application/msword',"application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/x-mspowerpoint.12",'application/x-mspowerpoint']:
                filenames_written_1 = self.process_file(filename)
            else:
                filenames_written_1 = [filename]


            for filename_written_1 in filenames_written_1:
                if filename_written_1[-3:] == "pdf":
                    transformation_dictionary["pdf_filename"] = filename_written_1
                if filename_written_1[-3:] == "txt":
                    transformation_dictionary["txt_filename"] = filename_written_1
                if filename_written_1[-2:] == "nt":
                    transformation_dictionary["ft_nt_filename"] = filename_written_1
                if filename_written_1[-7:] == "wc.html":
                    transformation_dictionary["ft_wc_filename"] = filename_written_1
                if filename_written_1[-7:] == "ne.html":
                    transformation_dictionary["ft_ne_filename"] = filename_written_1


                if "pdf_filename" in transformation_dictionary and pdf_done==False:
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

                        if filename_written_2[-3:] == "txt":
                            if "txt_filename" not in transformation_dictionary:
                                transformation_dictionary["txt_filename"] = filename_written_2
                            transformation_dictionary["pdf_texts"] = filename_written_2

                    pdf_done = True

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

            #Add transformation dictionary json as a mongo document property
            f = self.gridFSobj.get_version(filename=filename, version=-1)
            mime_type_file_name = mimetypes.guess_type(filename)[0]
            ts = time.time()
            self.gridFSobj.put(f, content_type = mime_type_file_name, filename = filename, time_stamp = ts, transformation_dictionary_json = json_file_name)
            self.gridFSobj.delete(f._id)

        except:
            print "Error processing document to end point: ", filename

        end_time = time.time()
        #print "Total processing time = ", end_time-start_time
        return transformation_dictionary

    #Clear transformations
    def clean_transformation_dictionary(self,filename):
        if(self.gridFSobj.exists(filename=filename+".json")):
            f = self.gridFSobj.get_last_version(filename+".json")
            json_file_id = f._id
            #content = f.read()
            json_content = json.load(f)

            l = json_content.get("png_large")
            if(l):
                for k in l:
                    if(self.gridFSobj.exists(filename=k)):
                        f = self.gridFSobj.get_last_version(k)
                        self.gridFSobj.delete(f._id)

            l = json_content.get("png_medium")
            if(l):
                for k in l:
                    if(self.gridFSobj.exists(filename=k)):
                        f = self.gridFSobj.get_last_version(k)
                        self.gridFSobj.delete(f._id)

            l = json_content.get("png_small")
            if(l):
                for k in l:
                    if(self.gridFSobj.exists(filename=k)):
                        f = self.gridFSobj.get_last_version(k)
                        self.gridFSobj.delete(f._id)

            l = json_content.get("png_originals")
            if(l):
                for k in l:
                    if(self.gridFSobj.exists(filename=k)):
                        f = self.gridFSobj.get_last_version(k)
                        self.gridFSobj.delete(f._id)

            l = json_content.get("tiff_originals")
            if(l):
                for k in l:
                    if(self.gridFSobj.exists(filename=k)):
                        f = self.gridFSobj.get_last_version(k)
                        self.gridFSobj.delete(f._id)

            k = json_content.get("txt_filename")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            k = json_content.get("pdf_filename")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            k = json_content.get("pdf_texts")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            k = json_content.get("ft_nt_filename")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            k = json_content.get("ft_wc_filename")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            k = json_content.get("ft_ne_filename")
            if(k):
                if(self.gridFSobj.exists(filename=k)):
                    f = self.gridFSobj.get_last_version(k)
                    self.gridFSobj.delete(f._id)

            self.gridFSobj.delete(json_file_id)


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
            if self.discover_entities_done==False:
                self.discover_entities(writing_location,full_text_file_name_written,files_created)
                self.discover_entities_done = True


        elif content_type == 'application/x-mspowerpoint.12' or content_type == 'application/x-mspowerpoint':
            file_name_written = self._convert_from_ppt_to_pdf(filename_to_write)
            os.path.basename(file_name_written)
            pdf_file_name_written = os.path.basename(file_name_written)
            self._upload_file(pdf_file_name_written,file_name_written)
            files_created.append(pdf_file_name_written)

        elif content_type == "application/pdf":
            for conversion_type in self.pdf_conversion_types:

                file_name_pairs = self._convert_pdf_to_other_format(filename_to_write, conversion_type, writing_location, files_created)
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


    #@author: Som Satapathy
    def discover_entities(self,writing_location,full_text_file_name_written,files_created):
        de_start_time = time.time()
        full_free_text_ntriples_file=os.path.join(writing_location,full_text_file_name_written[0:full_text_file_name_written.index(".")]+".free.text.nt")
        full_tkCount_file=os.path.join(writing_location,full_text_file_name_written[0:full_text_file_name_written.index(".")]+".free.text.tokencount.json")
        full_free_text_wordcloud_file=os.path.join(writing_location,full_text_file_name_written[0:full_text_file_name_written.index(".")]+".free.text.wc.html")
        full_free_text_ne_file=os.path.join(writing_location,full_text_file_name_written[0:full_text_file_name_written.index(".")]+".free.text.ne.html")

        self._generate_context_triples(full_text_file_name_written,full_free_text_ntriples_file,full_tkCount_file)
        self._generate_word_cloud(full_text_file_name_written,full_free_text_wordcloud_file)
        self._generate_named_entities(full_text_file_name_written,full_free_text_ne_file)

        free_text_ntriples_file = os.path.basename(full_free_text_ntriples_file)
        self._upload_file(free_text_ntriples_file, full_free_text_ntriples_file)
        files_created.append(free_text_ntriples_file)

        free_text_wordcloud_file = os.path.basename(full_free_text_wordcloud_file)
        self._upload_file(free_text_wordcloud_file, full_free_text_wordcloud_file)
        files_created.append(free_text_wordcloud_file)

        free_text_ne_file = os.path.basename(full_free_text_ne_file)
        self._upload_file(free_text_ne_file, full_free_text_ne_file)
        files_created.append(free_text_ne_file)

        de_end_time = time.time()
        #print "Discover entities time = ", de_end_time-de_start_time


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

    def _convert_pdf_to_other_format(self, file_name, conversion_type, writing_location, files_created):
        """Can convert a PDF file to png, tiff, and text formats"""
        #acrobat = win32.gencache.EnsureDispatch("AcroExch.App")
        #pdf = win32.gencache.EnsureDispatch("AcroExch.PDDoc")
        try:
            win32.gencache.EnsureModule('{FF76CB60-2E68-101B-B02E-04021C009402}', 0, 1, 1)
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

            #Using text to discover entities
            if conversion_type == "txt" and self.discover_entities_done==False:
                self.discover_entities(writing_location,converted_file_name,files_created)
                self.discover_entities_done = True
        except:
            traceback.print_exc()

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

        if image.mode == "P" or image.mode == "1":
            image = image.convert("L")
        #new_image = image.filter(ImageFilter.BLUR)
        new_image = image.resize((new_width,new_height), Image.ANTIALIAS)
        new_image_name = image_file_name + "." + image_suffix + "." + image_type.lower()
        new_image.save(new_image_name, image_type)
        return new_image_name

    def _process_acrobat_numbered_file_name(self, file_name):
        """Convert Acrobat exported file name 'sample5.pdf_Page_3.png' to 'sample5.pdf.3.png'"""

        cleaned_file_name = os.path.basename(file_name)
        parsed_file_name = cleaned_file_name.split("_Page_")
        if(len(parsed_file_name)>1):
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
        
    def _generate_context_triples(self,file_name,free_text_ntriples_file,tkCount_file):
            jData=dict()
            tokens=[]
            f=open(file_name)
            #encoding = open(file_name).encoding
            #f=codecs.open(file_name,'r',encoding=encoding)
            raw=f.read()
            #raw.decode("UTF-8")
            predicate="http://vivoweb.org/ontology/core#freetextKeyword"
            ntriples_file_name=free_text_ntriples_file  
            ts = pyTripleSimple.SimpleTripleStore()
            words = nltk.word_tokenize(raw)
            for word in words:
                try:
                    word.decode('utf-8')
                    subject="http://example.org/"+os.path.basename(f.name)
                    ts.add_triple(pyTripleSimple.SimpleTriple(subject, predicate, word, "uul"))
                    tokens.append(word)
                except :
                    continue
        
            f_nt = open(ntriples_file_name,'w')
            ts.export_to_ntriples_file(f_nt)
            
            st=set(words)
            for w in st:
                try:
                    w.decode('utf-8')
                    c=tokens.count(w)
                    jData[w]=c
                except :
                    continue

            #print repr(jData)
            jTokenCount=json.dumps(jData)
            data=[{'textVersion':os.path.basename(f.name),'nTriples.free.text':os.path.basename(f_nt.name),'unq.token.count':jTokenCount}]
            json_data=json.dumps(data)
            
            tkCount_file_to_write=open(tkCount_file,'w')
            tkCount_file_to_write.write(json_data)
            tkCount_file_to_write.close()
            
            f.close()
            f_nt.close()

    def _generate_word_cloud(self,ft_file,wc_file):
        f=open(ft_file)
        raw=f.read()
        wc = WordCloud.WordCloud()
        wc.addWords(raw)
        wc.cloud(wc_file)
        f.close()
        
    def _generate_named_entities(self,ft_file,ne_file):
        f=open(ft_file)
        raw=f.read()
        ne=NER.NER()
        ne.generate_named_entities(raw,ne_file)
        f.close()
    

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
