import streamlit as st 

st.title("Hello, Streamlit!")
uploader_file=st.file_uploader("Upload a file",type=["txt"],accept_multiple_files=False)
if uploader_file is not None:
    file_name=uploader_file.name
    file_type=uploader_file.type
    file_size=uploader_file.size
    st.write(f"File Name: {file_name}")
    st.write(f"File Type: {file_type}")
    st.write(f"File Size: {file_size} bytes")
    content=uploader_file.read().decode("utf-8")
    st.write("File Content:")
    st.text(content)


