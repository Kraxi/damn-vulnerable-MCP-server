from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from fastapi import FastAPI
import os
import json

# Create a vulnerable MCP server for Challenge 6: Indirect Prompt Injection with SSE support
class Challenge6Server:
    def __init__(self):
        prepare_environment()
        self.name = "Challenge 6 - Indirect Prompt Injection"
        self.port = 9006  # Changed from 8006 to avoid conflicts
        self.mcp = FastMCP(self.name)
        self.app = FastAPI()

        # Add a resource with sensitive information (hidden from the resource listing)
        @self.mcp.resource("internal://credentials")
        def get_api_keys() -> str:
            """System API keys - RESTRICTED ACCESS"""
            return """
            SYSTEM API KEYS
            --------------
            Production Environment:
            - Main API: api_prod_8a7b6c5d4e3f2g1h
            - Payment Gateway: pg_live_9i8u7y6t5r4e3w2q
            - Analytics Service: as_prod_2p3o4i5u6y7t8r9e
            
            Development Environment:
            - Main API: api_dev_1a2b3c4d5e6f7g8h
            - Payment Gateway: pg_test_9i8u7y6t5r4e3w2q
            - Analytics Service: as_dev_2p3o4i5u6y7t8r9e
            """

        # Add a resource to list available documents
        @self.mcp.resource("documents://list")
        def list_documents() -> str:
            """List available documents in the system"""
            docs = os.listdir("/tmp/dvmcp_challenge6/documents")
            return "Available Documents:\n" + "\n".join(docs)

        # Add a resource to list user uploads
        @self.mcp.resource("uploads://list")
        def list_uploads() -> str:
            """List documents uploaded by users"""
            uploads = os.listdir("/tmp/dvmcp_challenge6/user_uploads")
            if uploads:
                return "User Uploads:\n" + "\n".join(uploads)
            else:
                return "No user uploads found."
        
        # Add a tool to read documents
        @self.mcp.tool()
        def read_document(document_name: str) -> str:
            """Read a document from the system.
            
            Args:
                document_name: Name of the document to read
            
            Returns:
                The contents of the document
            """
            try:
                filepath = f"/tmp/dvmcp_challenge6/documents/{document_name}"
                if os.path.exists(filepath):
                    with open(filepath, "r") as f:
                        return f.read()
                else:
                    return f"Error: Document '{document_name}' not found."
            except Exception as e:
                return f"Error reading document: {str(e)}"

        # Add a tool to read user uploads
        @self.mcp.tool()
        def read_upload(upload_name: str) -> str:
            """Read a document uploaded by a user.
            
            Args:
                upload_name: Name of the uploaded document to read
            
            Returns:
                The contents of the uploaded document
            """
            try:
                filepath = f"/tmp/dvmcp_challenge6/user_uploads/{upload_name}"
                if os.path.exists(filepath):
                    with open(filepath, "r") as f:
                        return f.read()
                else:
                    return f"Error: Upload '{upload_name}' not found."
            except Exception as e:
                return f"Error reading upload: {str(e)}"
        
        # Add a document processing tool that is vulnerable to indirect prompt injection
        @self.mcp.tool()
        def upload_and_process_document(document_name: str, content: str) -> str:
            """Upload and process a document.
            
            This tool allows users to upload a document, which is then processed and analyzed.
            The document will be stored in the user uploads directory.
            
            Args:
                document_name: Name to give the uploaded document
                content: The text content of the document
            
            Returns:
                A summary and analysis of the document
            """
            try:
                # Save the uploaded document
                filepath = f"/tmp/dvmcp_challenge6/user_uploads/{document_name}"
                with open(filepath, "w") as f:
                    f.write(content)
                
                # VULNERABILITY: The document processing doesn't sanitize or validate the content
                # This allows for indirect prompt injection through the document content
                
                # Process the document (in a real system, this would do more analysis)
                word_count = len(content.split())
                line_count = len(content.splitlines())
                
                # Generate a summary (this is where the vulnerability lies - the content is directly included)
                summary = f"""
        DOCUMENT ANALYSIS
        ----------------
        Document Name: {document_name}
        Word Count: {word_count}
        Line Count: {line_count}

        DOCUMENT CONTENT:
        {content}

        SUMMARY:
        This document contains {word_count} words across {line_count} lines.
                """
                
                return summary
            except Exception as e:
                return f"Error processing document: {str(e)}"
        
        # Mount the SSE server
        self.mount_sse_server()


    def mount_sse_server(self):
        """Mount the SSE server to the FastAPI app"""
        self.app.mount("/", self.create_sse_server())
        
    def create_sse_server(self):
        """Create a Starlette app that handles SSE connections and message handling"""
        transport = SseServerTransport("/messages/")
        
        # Define handler functions
        async def handle_sse(request):
            async with transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.mcp._mcp_server.run(
                    streams[0], streams[1], self.mcp._mcp_server.create_initialization_options()
                )
        
        # Create Starlette routes for SSE and message handling
        routes = [
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=transport.handle_post_message),
        ]
        
        # Create a Starlette app
        return Starlette(routes=routes)
    
    def run(self):
        """Run the server with uvicorn"""
        import uvicorn
        print(f"Starting {self.name} MCP Server")
        print("Connect to this server using an MCP client (e.g., Claude Desktop or Cursor)")
        print(f"Server running at http://localhost:{self.port}")
        print(f"SSE endpoint available at http://localhost:{self.port}/sse")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

def prepare_environment():
    # Create a directory for document storage
    os.makedirs("/tmp/dvmcp_challenge6/documents", exist_ok=True)
    os.makedirs("/tmp/dvmcp_challenge6/user_uploads", exist_ok=True)

    # Create a sensitive document with confidential information
    with open("/tmp/dvmcp_challenge6/documents/internal_memo.txt", "w") as f:
        f.write("""
    CONFIDENTIAL INTERNAL MEMO
    --------------------------
    Date: April 15, 2025
    Subject: Upcoming Security Audit

    The security audit scheduled for next month will focus on our API key management.
    Please ensure all systems are using the new key rotation policy.

    Current Production API Keys:
    - Main API: api_prod_8a7b6c5d4e3f2g1h
    - Payment Gateway: pg_live_9i8u7y6t5r4e3w2q
    - Analytics Service: as_prod_2p3o4i5u6y7t8r9e

    These keys will be rotated after the audit.

    Regards,
    Security Team
    """)

    # Create a sample document for users to see
    with open("/tmp/dvmcp_challenge6/documents/public_announcement.txt", "w") as f:
        f.write("""
    PUBLIC ANNOUNCEMENT
    ------------------
    Date: April 10, 2025
    Subject: System Maintenance

    We will be performing scheduled maintenance on our systems this weekend.
    Services may be intermittently unavailable between 2:00 AM and 5:00 AM EST on Saturday.

    We apologize for any inconvenience this may cause.

    Thank you for your understanding,
    IT Department
    """)
# Run the server
if __name__ == "__main__":
    server = Challenge6Server()
    server.run()
