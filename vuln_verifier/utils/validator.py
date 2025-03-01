# utils/validator.py
# Professional input validation with detailed logging

import os
from utils.exceptions import ValidationError
from utils.logger import logger

def validate_csv_file(filepath):
    try:
        if not os.path.exists(filepath):
            raise ValidationError(f"CSV file {filepath} does not exist")
        if not filepath.endswith(".csv"):
            raise ValidationError("File must be a .csv file")
        logger.info(f"\033[92mValidated {filepath} as a valid CSV file\033[0m")
    except ValidationError as e:
        logger.error(f"\033[91mValidation error: {str(e)}\033[0m")
        raise