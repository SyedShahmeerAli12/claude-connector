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

"""

anchor = "    location / {\n        # misc headers\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        # don't use forwarded schema"

if anchor in content:
    content = content.replace(anchor, mcp_block + anchor, 1)
    open('/tmp/app.conf', 'w').write(content)
    print("Done - /mcp block added")
else:
    print("ERROR - anchor not found, config not changed")
