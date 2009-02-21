from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from google.appengine.ext.webapp import template
from google.appengine.ext import db

PARTSIZE = 9.8 * 1024 * 1024

class UploadedFile(db.Model):
  content = db.BlobProperty()
  filename = db.StringProperty()
  is_head = db.BooleanProperty()
  size = db.IntegerProperty()
  type = db.StringProperty()
  next = db.ReferenceProperty()

class UploadPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/upload.html', {}))

  def post(self):
    filelength = len(self.request.get('file'))
    firstkey = 0
    data = self.request.get('file')
    this = 0
    last = None
    while this < filelength:
      if this + PARTSIZE > filelength:
        next = filelength
      else:
        next = this + PARTSIZE
      uf = UploadedFile()
      part = data[this:next]
      uf.content = part
      uf.type = self.request.POST['file'].type
      uf.filename = self.request.POST['file'].filename
      uf.size = next - this
      this = next
      uf.put()
      if last:
          last.next = uf
          last.put()
      last = uf
      if firstkey == 0:
        firstkey = uf.key()    
    self.response.out.write(template.render('templates/uploaded.html',
             {'key': firstkey }))

class DownloadPage(webapp.RequestHandler):
  def get(self, id=None):
    if id:
      uf = UploadedFile.get_by_id(int(id))
      self.response.headers['Content-disposition'] = 'attechment; filename=%s'% uf.filename 
      self.response.headers['Content-Type'] = uf.type

      self.response.out.write(uf.content)
      while uf.next:
        uf = uf.next
        self.response.out.write(uf.content)
#      self.response.out.write(template.render('templates/uploaded.html', {'request': uf.filename, 'size': uf.size, 'key': uf.key()}))
      
class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/hello.html', {}))

application = webapp.WSGIApplication(
                                     [('/upload', UploadPage),
                                      ('/l/([0-9]+)', DownloadPage),
    ('/.*', UploadPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
