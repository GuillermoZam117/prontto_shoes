# Integration Tests for Pronto Shoes POS System

This directory contains integration tests for the Pronto Shoes catalog POS system. Unlike unit tests, these integration tests focus on testing how different components of the system work together.

## Test Structure

The integration tests are organized into several test files:

- **test_sales_workflow.py**: Tests the complete sales process from product creation, order processing, to inventory updates, as well as returns and discount application workflows.
- **test_inventory_workflow.py**: Tests inventory management workflows including transfers between stores and inventory adjustments.

## Running the Tests

To run all integration tests:

```bash
python manage.py test tests
```

To run a specific test file:

```bash
python manage.py test tests.test_sales_workflow
```

To run a specific test class:

```bash
python manage.py test tests.test_sales_workflow.SalesWorkflowIntegrationTest
```

To run a specific test method:

```bash
python manage.py test tests.test_sales_workflow.SalesWorkflowIntegrationTest.test_complete_sales_workflow
```

## Test Coverage

These integration tests focus on critical business workflows:

1. **Sales Workflow**
   - Complete order creation and processing
   - Application of customer discounts
   - Inventory updates after sales

2. **Returns Workflow**
   - Product return processing
   - Customer credit generation
   - Inventory updates after returns

3. **Discount Calculation**
   - Monthly discount assignment based on sales volume
   - Correct tier application 

4. **Inventory Management**
   - Transfers between stores
   - Inventory adjustments for discrepancies

## Test Design Principles

These integration tests follow these principles:

1. **End-to-end workflows**: Each test simulates a complete business process rather than isolated functionality.
2. **Database transactions**: Tests use Django's TransactionTestCase to ensure proper database handling.
3. **Real-world scenarios**: Tests are designed to reflect actual business use cases.
4. **Verification at multiple steps**: Tests verify the correct state of the system at various points in the workflow.

## Adding New Integration Tests

When adding new integration tests, follow these guidelines:

1. Create test files for distinct business workflows
2. Use TransactionTestCase for proper transaction management
3. Create comprehensive setUp methods with all required test data
4. Document each step within test methods using comments
5. Verify system state at multiple points during the workflow 