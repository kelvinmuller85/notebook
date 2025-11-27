# Picture Editor - Quick Test Guide

## How to Test the New Picture Editor Features

### Setup
1. Open the Note Book program
2. Select or create a note file
3. Add or open a picture template with an image

### Test 1: Text Box Creation

**Steps:**
1. Open a picture template (one with an image loaded)
2. Look for the new toolbar below the title bar
3. Click the **"Text"** button (should toggle/highlight)
4. Click anywhere on the image to place a text box
5. A dialog should appear asking for text content
6. Type some text (e.g., "This is a label")
7. Click OK

**Expected Result:**
- Text box appears on the image with the text you entered
- Text appears in a box with blue border (Description type by default)

### Test 2: Text Box Editing

**Steps:**
1. After creating a text box, it should be selected
2. Change the **"Font:"** size spinner to 24
3. Click the **"Color:"** color picker and select a different color
4. The text in the box should update in real-time

**Expected Result:**
- Font size changes immediately
- Text color changes to selected color

### Test 3: Text Box Type Selection

**Steps:**
1. Look at the **"Type:"** dropdown in the toolbar
2. It should show "Description" by default (blue border)
3. Change it to "Instruction"
4. Click Text button again and add another text box
5. This new box should have an orange border

**Expected Result:**
- Description boxes have blue borders (blue text)
- Instruction boxes have orange borders (orange text)
- Visual distinction helps AI know which requests action

### Test 4: Moving Text Boxes

**Steps:**
1. Click on an existing text box (to select it)
2. Click and drag it to a new position on the image
3. Release to place it in the new location

**Expected Result:**
- Text box moves smoothly with your mouse
- Snaps to new position when released

### Test 5: Resizing Text Boxes

**Steps:**
1. Select a text box
2. Move your cursor to one of the red handles (corners or edges)
3. Drag the handle to resize the box
4. Release to set the new size

**Expected Result:**
- Red resize handles appear around selected box
- Dragging corner handles resizes both width and height
- Dragging edge handles resize single dimension
- Text reflows within new size

### Test 6: Deleting Text Boxes

**Steps:**
1. Click on a text box to select it
2. Double-click it (or right-click if available)
3. A dialog should appear with a "Delete" button
4. Click the Delete button

**Expected Result:**
- Text box is removed from image
- No text box dialog shown if just double-clicked on empty area

### Test 7: Paint Bucket Fill

**Steps:**
1. Click the **"Fill"** button (paint bucket icon)
2. Select a color from the **"Color:"** color picker
3. Click on a solid-colored area of the image
4. The fill tool should fill that color region

**Expected Result:**
- Clicking on a solid color region replaces all connected pixels of similar color
- The new color fills the entire continuous region
- Boundaries with different colors are respected
- Works like Paint 3D's fill tool

### Test 8: Save and Reload

**Steps:**
1. Add several text boxes with different types and colors
2. Use the paint bucket to fill some areas
3. Click the "Done" button (or close the picture editor)
4. Save the note using File → Save or Ctrl+S
5. Close the picture note window
6. Reopen the same picture template from the list
7. Click Open

**Expected Result:**
- All text boxes you created are still there
- Text, formatting, and colors are preserved
- Paint bucket changes are saved to the image
- Everything looks exactly as you left it

### Test 9: Multiple Text Boxes

**Steps:**
1. Add 3-4 text boxes to different areas of an image
2. Make them different types (2 description, 1-2 instruction)
3. Use different colors for each
4. Use different font sizes for each
5. Arrange them around different parts of the image

**Expected Result:**
- All boxes display correctly with their respective properties
- No overlap issues or rendering problems
- Each box maintains its own settings
- Visual hierarchy is clear

### Test 10: Integration with Note Features

**Steps:**
1. Open a picture template with text boxes
2. Check that the note menu buttons work:
   - Save to Note File
   - Save as Subset
   - Duplicate Note
   - Settings button (color change, etc.)
3. Verify they work without interfering with editor

**Expected Result:**
- All existing note features continue to work
- No errors when using menus
- Editor toolbar doesn't block access to note controls

## Troubleshooting

### No toolbar appears
- Make sure the program restarted after the update
- Check that picture_editor.py is in the src folder
- Verify note_picture.py was updated correctly

### Text doesn't appear
- Make sure you clicked OK in the text dialog
- Try clicking on the text box to edit it
- Check font size is visible (try size 16 or larger)

### Fill doesn't work
- Make sure Fill button is toggled on (should appear highlighted)
- Try clicking on a solid-color area (not edges with gradient)
- The color must be reasonably uniform

### Text boxes don't save
- Make sure to click "Done" or close the note properly
- Save the note using File menu or Ctrl+S
- Check that the note is being saved to a file (not just as a temp note)

## Expected Behavior Summary

| Feature | Expected | Icon |
|---------|----------|------|
| Text Tool | Click image to add labeled boxes | Text Icon |
| Fill Tool | Click areas to fill with color | Bucket Icon |
| Font Size | Adjust text size 8-72pt | Spinner |
| Color | Change text/fill color | Color Button |
| Text Type | Description (blue) vs Instruction (orange) | Dropdown |
| Done | Exit editor, return to view mode | Close Icon |

## Performance Notes

- Text boxes should render smoothly
- Dragging should have no lag
- Fill operations may take 1-2 seconds on large images
- All operations should be responsive without freezes

## Next Level Features (Phase 2)

These weren't in Phase 1 but could be added:
- [ ] Undo/Redo for text box and fill operations
- [ ] Copy/Paste text boxes
- [ ] Grid/alignment helpers
- [ ] Text box templates/presets
- [ ] Keyboard shortcuts (Delete key to remove box)
- [ ] Multiple selection
- [ ] Text alignment (left/center/right)
- [ ] Bold/italic text formatting

## Report Issues

If you find any of the following, please report:
1. Text boxes not saving
2. Paint bucket not filling
3. UI elements missing or misaligned
4. Colors not applying
5. Performance issues
6. Crashes or errors

Provide:
- Steps to reproduce
- Screenshot if possible
- Error messages from terminal
