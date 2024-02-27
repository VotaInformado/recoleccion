from django.http import HttpResponse


def read_file(request):
    f = open("static/certificate/74B3E853F16E32C8F625E917F6157A17.txt", "r")
    file_content = f.read()
    f.close()
    return HttpResponse(file_content, content_type="text/plain")
