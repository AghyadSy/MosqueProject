#!/usr/bin/env python
from decimal import Decimal
from core.models import calculate_memorization_points

# Test the memorization calculation
test_values = ['0.50', '1.50', '2.50', '3.50', '4.50', '5.50']
for pages in test_values:
    result = calculate_memorization_points(Decimal(pages))
    print(f"{pages} pages => {result} points")
