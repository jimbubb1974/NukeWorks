"""
Technology Vendor Forms
WTForms for vendor CRUD operations with validation
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.utils.validators import (
    validate_string_field,
    validate_unique_vendor_name,
    ValidationError as CustomValidationError
)


class VendorForm(FlaskForm):
    """Form for creating and editing technology vendors"""

    vendor_name = StringField(
        'Vendor Name',
        validators=[
            DataRequired(message="Vendor name is required"),
            Length(min=1, max=255, message="Vendor name must be between 1 and 255 characters")
        ],
        render_kw={"placeholder": "e.g., NuScale Power, X-energy"}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=10000, message="Notes cannot exceed 10,000 characters")],
        render_kw={"rows": 5, "placeholder": "Optional notes about the vendor"}
    )

    submit = SubmitField('Save Vendor')

    def __init__(self, vendor_id=None, *args, **kwargs):
        """
        Initialize form

        Args:
            vendor_id: ID of vendor being edited (None for new vendor)
        """
        super(VendorForm, self).__init__(*args, **kwargs)
        self.vendor_id = vendor_id

    def validate_vendor_name(self, field):
        """
        Validate vendor name using custom validators

        Checks:
        - String format and length (already done by WTForms)
        - Uniqueness (case-insensitive)
        """
        try:
            # Validate string format
            cleaned_name = validate_string_field(
                field.data,
                "vendor_name",
                max_length=255,
                required=True
            )

            # Update field data with cleaned value
            field.data = cleaned_name

            # Check uniqueness
            validate_unique_vendor_name(cleaned_name, vendor_id=self.vendor_id)

        except CustomValidationError as e:
            raise ValidationError(str(e))

    def validate_notes(self, field):
        """Validate notes field"""
        if field.data:
            try:
                cleaned_notes = validate_string_field(
                    field.data,
                    "notes",
                    max_length=10000,
                    required=False,
                    allow_newlines=True
                )
                field.data = cleaned_notes
            except CustomValidationError as e:
                raise ValidationError(str(e))


class DeleteVendorForm(FlaskForm):
    """Form for deleting a vendor (CSRF protection)"""
    submit = SubmitField('Confirm Delete')
