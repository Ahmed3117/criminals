from django.db import models

class Criminal(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='criminals/')
    is_criminal = models.BooleanField(default=False)

    def __str__(self):
        return self.name
