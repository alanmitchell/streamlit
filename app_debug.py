"""Use this module for development with VS Code and the integrated debugger"""
import debugpy
import streamlit as st

import app

# pylint: disable=invalid-name
markdown = st.markdown(
    """
## Ready to attach the VS Code Debugger!

![Python: Remote Attach](https://awesome-streamlit.readthedocs.io/en/latest/_images/vscode_python_remote_attach.png)

for more info see the [VS Code section at awesome-streamlit.readthedocs.io]
(https://awesome-streamlit.readthedocs.io/en/latest/vscode.html#integrated-debugging)
"""
)

debugpy.listen(('localhost', 5678))
debugpy.wait_for_client()

markdown.empty()

app.main()
