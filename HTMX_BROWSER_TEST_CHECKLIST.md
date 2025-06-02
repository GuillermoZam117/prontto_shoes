# HTMX Browser Testing Checklist - Productos Module

## TEST ENVIRONMENT
- **Server**: http://127.0.0.1:8000/
- **Module**: Productos (/productos/)
- **Database**: 106 productos available for testing
- **Browser**: VS Code Simple Browser

## 🔍 SEARCH FUNCTIONALITY TESTS

### ✅ Test 1: Search by Codigo
- [ ] Enter "VAN" in search field
- [ ] Verify 300ms delay (observe loading indicator)
- [ ] Confirm results show Vans products
- [ ] Clear search and verify full list returns

### ✅ Test 2: Search by Marca
- [ ] Enter "Nike" in search field
- [ ] Verify HTMX request to /productos/?search=Nike
- [ ] Confirm only Nike products appear
- [ ] Test case insensitive: "nike"

### ✅ Test 3: Search by Modelo
- [ ] Enter "Comfort" in search field
- [ ] Verify Converse Comfort and Reebok Comfort appear
- [ ] Test partial matching: "Com"

### ✅ Test 4: Search by Color
- [ ] Enter "Blanco" in search field
- [ ] Verify products with white color appear
- [ ] Test partial matching: "Blan"

### ✅ Test 5: Search Performance
- [ ] Type rapidly and verify debouncing (300ms delay)
- [ ] Verify loading spinner appears during search
- [ ] Confirm search works with special characters

## 🔧 FILTER FUNCTIONALITY TESTS

### ✅ Test 6: Temporada Filter
- [ ] Select different temporada options
- [ ] Verify HTMX request includes temporada parameter
- [ ] Confirm results filter correctly
- [ ] Test "Todos" option resets filter

### ✅ Test 7: Oferta Filter
- [ ] Toggle oferta filter (Sí/No/Todos)
- [ ] Verify HTMX request includes oferta parameter
- [ ] Confirm only productos en oferta appear when "Sí"

### ✅ Test 8: Catalogo Filter
- [ ] Select different catalogo options
- [ ] Verify HTMX request includes catalogo parameter
- [ ] Confirm results filter correctly

### ✅ Test 9: Precio Range Filter
- [ ] Test minimum price filter
- [ ] Test maximum price filter
- [ ] Test both min and max together
- [ ] Verify numeric validation

### ✅ Test 10: Combined Filters
- [ ] Apply search + temporada filter
- [ ] Apply multiple filters simultaneously
- [ ] Verify all parameters in HTMX request
- [ ] Test clearing individual filters

## 📋 CRUD FUNCTIONALITY TESTS

### ✅ Test 11: Product Detail View
- [ ] Click "Ver" button on a product
- [ ] Verify HTMX modal/detail opens
- [ ] Confirm all product information displays
- [ ] Test modal close functionality

### ✅ Test 12: Product Edit
- [ ] Click "Editar" button on a product
- [ ] Verify edit form loads via HTMX
- [ ] Make a change and save
- [ ] Confirm list updates without page reload

### ✅ Test 13: Product Delete
- [ ] Click "Eliminar" button on a product
- [ ] Verify confirmation dialog appears
- [ ] Confirm delete with HTMX request
- [ ] Verify product removed from list instantly
- [ ] Test cancel delete operation

### ✅ Test 14: Product Create
- [ ] Click "Nuevo Producto" button
- [ ] Verify create form loads via HTMX
- [ ] Fill form and submit
- [ ] Confirm new product appears in list

## 📊 UI/UX FUNCTIONALITY TESTS

### ✅ Test 15: Dashboard Cards
- [ ] Verify summary cards show correct counts
- [ ] Check cards update after filters applied
- [ ] Confirm responsive design on different screen sizes

### ✅ Test 16: Loading States
- [ ] Verify loading spinner during HTMX requests
- [ ] Check loading states don't block UI
- [ ] Confirm loading indicators disappear after response

### ✅ Test 17: Pagination
- [ ] Test pagination with large result sets
- [ ] Verify HTMX requests preserve filters
- [ ] Test first/last/next/previous buttons

### ✅ Test 18: Error Handling
- [ ] Test network error scenarios
- [ ] Verify 404 errors handled gracefully
- [ ] Test invalid input handling

### ✅ Test 19: Browser Back/Forward
- [ ] Apply filters and use browser back
- [ ] Verify state preservation or reset
- [ ] Test bookmarking filtered URLs

### ✅ Test 20: Mobile Responsiveness
- [ ] Test on mobile viewport
- [ ] Verify touch interactions work
- [ ] Check responsive filter layout

## 🔧 TECHNICAL VERIFICATION TESTS

### ✅ Test 21: HTMX Headers
- [ ] Open browser dev tools
- [ ] Verify HX-Request headers present
- [ ] Check HX-Target headers
- [ ] Confirm partial template responses

### ✅ Test 22: Performance
- [ ] Monitor network tab for efficient requests
- [ ] Verify only necessary DOM updates
- [ ] Check for memory leaks with repeated actions

### ✅ Test 23: Cross-browser Compatibility
- [ ] Test basic functionality in Chrome
- [ ] Verify critical features work in Firefox
- [ ] Check Safari compatibility (if available)

---

## TEST RESULTS SUMMARY

**Date**: ___________
**Tester**: ___________
**Browser**: VS Code Simple Browser
**Pass Rate**: _____ / 23 tests

### Critical Issues Found:
- [ ] Issue 1: ________________________________
- [ ] Issue 2: ________________________________
- [ ] Issue 3: ________________________________

### Minor Issues Found:
- [ ] Issue 1: ________________________________
- [ ] Issue 2: ________________________________

### Performance Notes:
- Search delay: _____ ms (target: 300ms)
- Filter response time: _____ ms
- Page load time: _____ ms

### Overall Assessment:
- [ ] ✅ Ready for production
- [ ] ⚠️ Minor fixes needed
- [ ] ❌ Major issues require attention

---

## COMPARISON WITH PROVEEDORES MODULE
Compare functionality and performance with the successfully implemented proveedores module to ensure consistency.

**Notes**:
_Add any additional observations or recommendations here._
