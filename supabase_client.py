import os

from supabase import Client, create_client

SUPABASE_URL = "https://kglmqccktedjuapttmwg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtnbG1xY2NrdGVkanVhcHR0bXdnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzMDM2NDcsImV4cCI6MjA1NTg3OTY0N30.CeFQotypcW3AhDspXVSj892LSDLyf-0yGizoKCFMB40"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
