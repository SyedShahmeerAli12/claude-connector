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

"""

anchor = "    location / {\n        # misc headers"

if anchor in content:
    # Only add if not already present
    if "location /mcp" not in content:
        content = content.replace(anchor, mcp_block + anchor, 1)
        open('/tmp/app.conf', 'w').write(content)
        print("Done - /mcp and .well-known blocks added")
    elif "oauth-authorization-server" not in content:
        # /mcp exists but .well-known doesn't — add just the .well-known block
        well_known_block = """    location /.well-known/oauth-authorization-server {
        proxy_pass http://mcp-app:8000/.well-known/oauth-authorization-server;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

"""
        content = content.replace(anchor, well_known_block + anchor, 1)
        open('/tmp/app.conf', 'w').write(content)
        print("Done - .well-known block added")
    else:
        print("Both blocks already present, no changes made")
else:
    print("ERROR - anchor not found, config not changed")
