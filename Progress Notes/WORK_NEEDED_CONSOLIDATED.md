# Work Needed - Development Tasks and Issues

**Date**: November 12, 2025  
**Consolidated From**: REMAINING_ISSUES.md and next-steps planning  
**Priority Tiers**: Critical → High → Medium

---

## Critical Issues (Fix Immediately)

### 1. Code Editor Icon Issues
**File**: `Files/src/note_extended.py`  
**Severity**: Critical - UI Confusion  

**Problem**:
- Left icon (color droplet) shows "Convert to Text" functionality
- Should show code note color selector instead
- Users confused about purpose

**Solution Required**:
- Modify icon click handler to change note color (like picture notes)
- Keep note type as code, just change the color
- Move "Convert to Text" to second icon position

**Acceptance Criteria**:
- ✓ Left icon changes note color without conversion
- ✓ Second icon converts to text AND opens color menu
- ✓ Gutter color updates when converting

**Estimated Effort**: 30-45 minutes

---

### 2. Gutter Color on Conversion
**File**: `Files/src/note_code.py`  
**Severity**: Critical - Data Loss  

**Problem**:
- When converting text note to code note, gutter color turns yellow
- Should inherit the note's selected color
- Causes visual inconsistency

**Root Cause**:
- GtkSourceView syntax highlighting overrides color
- Need to apply color AFTER syntax highlighting setup

**Solution Required**:
- Modify code that applies colors in note_code.py
- Set gutter color after GtkSourceView initialization
- Test with all 11 colors

**Acceptance Criteria**:
- ✓ Gutter color matches note color after conversion
- ✓ Works for all 11 colors
- ✓ Persists across save/reload

**Estimated Effort**: 20-30 minutes

---

## High Priority Issues (Fix This Session)

### 3. Plus Button Menu System
**File**: `Files/src/notebook_wrapper.py` (~line 242-266)  
**Severity**: High - Core Workflow  

**Problem**:
- Plus (+) button directly creates new note
- Should have dropdown menu with two options:
  1. "New Note" - Create blank note of same type
  2. "Duplicate" - Copy note with all content

**Current Behavior**:
```
User clicks + → Creates blank note
```

**Expected Behavior**:
```
User clicks + → Menu appears:
  ├─ New Note (creates blank)
  └─ Duplicate (copies selected note)
```

**Implementation Steps**:
1. Change button to MenuButton instead of Button
2. Create Gtk.Menu with two Gtk.MenuItem options
3. "New Note" calls existing create_new_note logic
4. "Duplicate" calls duplicate_note with current note
5. Handle case when no note selected (disable Duplicate)

**Acceptance Criteria**:
- ✓ Plus button shows menu on click
- ✓ "New Note" creates blank note
- ✓ "Duplicate" copies selected note with all content
- ✓ "Duplicate" disabled when no note selected
- ✓ Menu closes after selection

**Estimated Effort**: 1-1.5 hours

---

### 4. Save/Refresh Functionality
**Files**: `Files/src/notebook_wrapper.py`, `Files/src/note_code.py`  
**Severity**: High - Data Integrity  

**Problem**:
- Code notes may not save properly
- Note list may not refresh after save
- Changes sometimes lost when switching between notes

**Current Issues**:
- No confirmation that save succeeded
- List doesn't update to show note title/content
- No error handling if save fails

**Solution Required**:
1. Add validation before save:
   - Check note has required fields
   - Verify file permissions
   - Handle save errors with user feedback

2. Add post-save refresh:
   - Update note list display
   - Show confirmation toast
   - Clear unsaved changes indicator

3. Test scenarios:
   - Save new note
   - Update existing note
   - Save code note with syntax
   - Save text note with formatting
   - Save picture note with edits

**Implementation Details**:
```python
def save_note_to_file(self, note):
    """Save with validation and feedback"""
    try:
        # Validate note
        if not self._validate_note(note):
            self._toast("Cannot save: Invalid note")
            return False
        
        # Save to file
        note_data = note.get_note_data()
        note_path = os.path.join(DATA_DIR, f"note_{note_data['id']}.json")
        with open(note_path, 'w') as f:
            json.dump(note_data, f, indent=2)
        
        # Refresh UI
        self._refresh_note_list()
        self._toast(f"Note saved: {note.title or 'Untitled'}")
        return True
    except Exception as e:
        self._toast(f"Save failed: {e}")
        logging.error(f"Save error: {e}")
        return False
```

**Acceptance Criteria**:
- ✓ All notes save without data loss
- ✓ List refreshes immediately after save
- ✓ User sees success/error feedback
- ✓ Works for all note types
- ✓ Handle disk full, permission errors

**Estimated Effort**: 1.5-2 hours

---

## Medium Priority Issues (Next Session)

### 5. Picture Note Template Browsing
**File**: `Files/src/notebook_wrapper.py`  
**Severity**: Medium - Enhancement  

**Problem**:
- Can't browse available picture templates easily
- No thumbnail preview before selecting
- Hard to find specific template

**Proposed Solution**:
1. Add "Template Gallery" button
2. Show thumbnails of all available templates
3. Click thumbnail to create note from that template
4. Show template names/descriptions

**Estimated Effort**: 2-3 hours

---

### 6. Code Note Syntax Highlighting Themes
**Files**: `Files/src/note_code.py`, `Files/ui/sticky.css`  
**Severity**: Medium - Enhancement  

**Problem**:
- Limited syntax highlighting color schemes
- Should support multiple themes
- Dark mode not available

**Proposed Solution**:
1. Add theme selector to settings
2. Create light and dark theme variants
3. Store theme preference
4. Apply on note open

**Estimated Effort**: 1.5-2 hours

---

### 7. Search/Filter Notes
**File**: `Files/src/notebook_wrapper.py`  
**Severity**: Medium - Usability  

**Problem**:
- Can't search for notes by title or content
- Can't filter by note type or color
- Scrolling through many notes is tedious

**Proposed Solution**:
1. Add search box in UI
2. Filter notes as user types
3. Add filter buttons (by type, color)
4. Highlight matching text

**Estimated Effort**: 2-2.5 hours

---

## Documentation Issues

### 8. Update Main Documentation
**Files**: Root directory *.md files  
**Severity**: Low - Documentation  

**Required Updates**:
1. Update FEATURE_REQUIREMENTS.md with completed items
2. Update PROJECT_STATUS.md with current progress
3. Archive completed implementation plans
4. Create next-phase requirements

**Estimated Effort**: 30-45 minutes

---

## Testing Checklist

### Before Marking Issue as "Done"

**Icon Fix**:
- [ ] Left icon doesn't convert notes
- [ ] Left icon changes color
- [ ] Second icon converts and opens menu
- [ ] Works for all note types
- [ ] Gutter color updates correctly

**Plus Button Menu**:
- [ ] Menu appears on click
- [ ] New Note creates blank
- [ ] Duplicate works with all content types
- [ ] Disabled when no selection
- [ ] Menu disappears after selection

**Save/Refresh**:
- [ ] Text notes save
- [ ] Code notes save
- [ ] Picture notes save
- [ ] List updates after save
- [ ] Title shows correct content
- [ ] Errors display toast message
- [ ] Works with special characters

---

## Summary Table

| Issue | Priority | Effort | Files | Status |
|-------|----------|--------|-------|--------|
| Code icon bug | Critical | 30-45min | note_extended.py | NOT STARTED |
| Gutter color bug | Critical | 20-30min | note_code.py | NOT STARTED |
| Plus menu system | High | 1-1.5hr | notebook_wrapper.py | NOT STARTED |
| Save/refresh | High | 1.5-2hr | notebook_wrapper.py, note_code.py | NOT STARTED |
| Template gallery | Medium | 2-3hr | notebook_wrapper.py | NOT STARTED |
| Syntax themes | Medium | 1.5-2hr | note_code.py, sticky.css | NOT STARTED |
| Search/filter | Medium | 2-2.5hr | notebook_wrapper.py | NOT STARTED |
| Documentation | Low | 30-45min | Root *.md files | NOT STARTED |

---

## Recommended Work Order

### This Session (Est. 3-4 hours total)
1. **Code icon bug** (Critical, 30-45min)
2. **Gutter color bug** (Critical, 20-30min)
3. **Plus button menu** (High, 1-1.5hr)
4. **Save/refresh** (High, 1.5-2hr)

### Next Session (Est. 4-5 hours)
5. **Template gallery** (Medium, 2-3hr)
6. **Syntax themes** (Medium, 1.5-2hr)
7. **Search/filter** (Medium, 2-2.5hr)

---

## Notes for Developers

### Code Icon Issue Specifics
- Location: `note_extended.py` line ~70-90 (icon click handler)
- Current: Opens convert dialog
- Needed: Call color picker instead
- Reference: How picture notes handle color (in `note_picture.py`)

### Save Issue Specifics
- Main save method: `notebook_wrapper.py` line 441-470
- Check: Test with code notes containing syntax characters
- Test: Large notes (>10KB)
- Test: Notes with special characters/unicode

### Plus Button Specifics
- Current button location: `notebook_wrapper.py` line ~240
- Create: Gtk.MenuButton instead of Gtk.Button
- Duplicate method exists at: `notebook_wrapper.py` line 418-440

---

## Success Criteria for Completion

Once all critical issues are fixed:
- ✓ Users never lose data during save
- ✓ UI accurately reflects application state
- ✓ All buttons do what their icons suggest
- ✓ No visual inconsistencies (gutter color matches)
- ✓ Basic workflow is intuitive (+ button has menu)
- ✓ Next development phase unblocked

