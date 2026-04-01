from langchain_community.document_loaders import PyPDFLoader

loader=PyPDFLoader(file_path="test.pdf",mode="single")
i=0
result=loader.load()
for doc in result:
    i+=1
    print(doc.page_content)
    print('*'*30,i)



