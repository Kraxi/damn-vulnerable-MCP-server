from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from fastapi import FastAPI
import os

# Create a vulnerable MCP server for Challenge 3: Excessive Permission Scope with SSE support
class Challenge3Server:
    def __init__(self):
        
        prepare_environment()
        
        self.name = "Challenge 3 - Excessive Permission Scope"
        self.port = 9003  # Changed from 8003 to avoid conflicts
        self.mcp = FastMCP(self.name)
        self.app = FastAPI()

        # Add a tool with excessive permissions
        @self.mcp.tool()
        def file_manager(action: str, path: str) -> str:
            """File manager tool that can read, write, and delete files
            
            Args:
                action: The action to perform (read, write, delete)
                path: The file path to operate on
            """
            import os
            
            # Vulnerable: No proper path validation or permission checks
            if action == "read":
                try:
                    with open(path, 'r') as f:
                        return f.read()
                except Exception as e:
                    return f"Error reading file: {str(e)}"
            elif action == "write":
                try:
                    with open(path, 'w') as f:
                        f.write("New content written by file manager")
                    return f"Successfully wrote to {path}"
                except Exception as e:
                    return f"Error writing to file: {str(e)}"
            elif action == "delete":
                try:
                    os.remove(path)
                    return f"Successfully deleted {path}"
                except Exception as e:
                    return f"Error deleting file: {str(e)}"
            else:
                return f"Invalid action: {action}. Must be one of: read, write, delete"
        
        # Add a tool to search for files (with excessive permissions - can search anywhere)
        @self.mcp.tool()
        def search_files(keyword: str) -> str:
            """Search for files containing a specific keyword in the public directory.
            
            Args:
                keyword: The keyword to search for
            
            Returns:
                List of files containing the keyword
            """
            # VULNERABILITY: This tool searches both public and private directories
            # It should only search the public directory
            
            results = []
            
            # Search in public directory
            for filename in os.listdir("/tmp/dvmcp_challenge3/public"):
                filepath = f"/tmp/dvmcp_challenge3/public/{filename}"
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                        if keyword.lower() in content.lower():
                            results.append(f"Public/{filename}")
                except:
                    pass
            
            # VULNERABILITY: Also searches in private directory
            for filename in os.listdir("/tmp/dvmcp_challenge3/private"):
                filepath = f"/tmp/dvmcp_challenge3/private/{filename}"
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                        if keyword.lower() in content.lower():
                            results.append(f"Private/{filename}")
                except:
                    pass
            
            if results:
                return f"Files containing '{keyword}':\n" + "\n".join(results)
            else:
                return f"No files found containing '{keyword}'."
        
        # Add a resource for public files
        @self.mcp.resource("public://{filename}")
        def get_public_file(filename: str) -> str:
            """Get a public file"""
            import os
            
            public_dir = "/tmp/dvmcp_challenge3/public"
            file_path = os.path.join(public_dir, filename)
            
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading public file: {str(e)}"
        
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
    # Create a directory structure for the challenge
    os.makedirs("/tmp/dvmcp_challenge3/public", exist_ok=True)
    os.makedirs("/tmp/dvmcp_challenge3/private", exist_ok=True)

    # Create some public files
    with open("/tmp/dvmcp_challenge3/public/welcome.txt", "w") as f:
        f.write("Welcome to the ACME Corp file system. Public files are stored here.")

    with open("/tmp/dvmcp_challenge3/public/company_overview.txt", "w") as f:
        f.write("ACME Corporation is a leading provider of technology solutions.")

    # Create sensitive files in the private directory
    with open("/tmp/dvmcp_challenge3/private/employee_salaries.txt", "w") as f:
        f.write("""
    CONFIDENTIAL: Employee Salary Information
    -----------------------------------------
    CEO: $1,200,000/year
    CTO: $950,000/year
    CFO: $900,000/year
    Senior Engineers: $180,000-$250,000/year
    Mid-level Engineers: $120,000-$170,000/year
    Junior Engineers: $80,000-$110,000/year
    """)

    with open("/tmp/dvmcp_challenge3/private/acquisition_plans.txt", "w") as f:
        f.write("""
    TOP SECRET: Upcoming Acquisition Plans
    -------------------------------------
    Target Company: InnoTech Solutions
    Planned Offer: $500 million
    Expected Closing: Q3 2025
    Synergy Opportunities:
    - Integrate their AI platform with our cloud services
    - Consolidate sales and marketing teams (estimated 15% reduction)
    - Migrate their customers to our infrastructure
    """)

    with open("/tmp/dvmcp_challenge3/private/system_credentials.txt", "w") as f:
        f.write("""
    SYSTEM CREDENTIALS - HIGHLY RESTRICTED
    -------------------------------------
    Production Database: 
    Host: db.acmecorp.internal
    Username: admin_prod
    Password: Pr0d-DB-S3cret!

    Cloud Infrastructure:
    Account ID: ACME-CLOUD-92731
    API Key: ak_live_7y2JHGd8sKlM9nPzXqRt5vWx
    Secret: cs_live_bNp5T2vR8sKlM9nQzXwJhGf4
    """)

# Run the server
if __name__ == "__main__":
    server = Challenge3Server()
    server.run()
