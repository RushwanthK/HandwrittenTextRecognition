import cv2
import streamlit as st
import os
image_file = st.file_uploader("Upload An Image",type=['png','jpeg','jpg'])
if image_file is not None:
    file_details = {"FileName":image_file.name,"FileType":image_file.type}
    st.write(file_details)
    #img = cv2.imread(image_file)
    st.image(image_file)
    '''with open(os.path.join("/content/drive/MyDrive/SimpleHTR/data",image_file.name),"wb") as f: 
      f.write(image_file.getbuffer())
      st.title(f[0])'''
    path = os.path.join("/content/drive/MyDrive/SimpleHTR/data",image_file.name)
    st.title(path)
    st.success("Saved File")