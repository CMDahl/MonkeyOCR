import os

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeResult, AnalyzeDocumentRequest,AnalyzeOutputOption

from azure.ai.documentintelligence.models import DocumentContentFormat
import os
import sys
from pathlib import Path

# Add the parent directory to the path
try:
    # VS code interactive window
    parent_dir = str(Path(__name__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
except:    
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Now import using a non-relative import
from key_vault import KeyVault


keyvault = KeyVault()
endpoint = keyvault.get_key("SDUAzureDocIntelligenceEndpoint")
key = keyvault.get_key("SDUAzureDocIntelligenceKey")
document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def get_ocr(path):
    with open(path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout",
        body=f,        
        output_content_format=DocumentContentFormat.MARKDOWN,             
        output=[AnalyzeOutputOption.FIGURES],
        content_type="application/octet-stream",
    )
    result: AnalyzeResult = poller.result()
    return result

if __name__ == "__main__":
    path = r"d:\GitHub\rma_ocr\data\tba\digibok_2007031501007_0432.jpg"
    result = get_ocr(path)
    print(result.content)
