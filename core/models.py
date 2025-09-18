from django.db import models

class XrayAnalysis(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    image = models.ImageField(upload_to="xrays/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    ai_results = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)  # Store error details
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "X-ray Analysis"
        verbose_name_plural = "X-ray Analyses"

    def __str__(self):
        return f"XrayAnalysis {self.id} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def is_completed(self):
        return self.status == "completed"

    @property
    def has_results(self):
        return self.ai_results is not None