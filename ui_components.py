import streamlit as st

def display_existing_files(files, delete_file_callback):
    st.write("Existing Files:")
    for file in files:
        col1, col2 = st.columns([3, 2])

        with col1:
            # Show summary on click
            if st.button(file['filename'], key=f"show_summary_{file['filename']}"):
                st.write(f"Filename: {file['filename']}")
                st.write(f"Summary: {file['summary']}")

        with col2:
            if st.button("Delete", key=f"delete_{file['filename']}"):
                delete_file_callback(file['filename'])
                st.success(f"File {file['filename']} deleted successfully")
