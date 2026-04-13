import subprocess

content = open('/tmp/app.conf').read()

mcp_block = """    location /mcp {
        proxy_pass http://mcp-app:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    location /.well-known/oauth-authorization-server {
        proxy_pass http://mcp-app:8000/.well-known/oauth-authorization-server;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /mcp-docs {
        proxy_pass http://mcp-app:8000/mcp-docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /mcp-privacy {
        proxy_pass http://mcp-app:8000/mcp-privacy;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

"""

anchor = "    location / {\n        # misc headers"

if anchor in content:
    if "location = /mcp-privacy" in content:
        print("All blocks already present, no changes made")
    else:
        # Remove old partial blocks and reinsert full set cleanly
        # Strip any previously inserted mcp/well-known blocks before anchor
        import re
        # Remove everything we previously inserted before the anchor
        content = re.sub(
            r'(    location /mcp \{.*?\}\n\n|'
            r'    location /\.well-known/oauth-authorization-server \{.*?\}\n\n|'
            r'    location = /docs \{.*?\}\n\n|'
            r'    location = /privacy \{.*?\}\n\n|'
            r'    location = /mcp-docs \{.*?\}\n\n|'
            r'    location = /mcp-privacy \{.*?\}\n\n)',
            '', content, flags=re.DOTALL
        )
        content = content.replace(anchor, mcp_block + anchor, 1)
        open('/tmp/app.conf', 'w').write(content)
        print("Done - all MCP blocks added")
else:
    print("ERROR - anchor not found, config not changed")
