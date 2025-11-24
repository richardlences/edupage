# Edupage Lunch App - Known Issues

## Critical: Edupage-API Bug 🐛

### Issue Description

The `edupage-api` Python library (version 0.12.3) has a bug in its meal parsing code that prevents it from properly loading past lunches and showing ordered meal status.

**Error:**
```python
File "edupage_api/lunches.py", line 178, in parse_meal
    [quality, quantity] = rating
TypeError: cannot unpack non-iterable NoneType object
```

### Root Cause

In the file `edupage_api/lunches.py` at line 178, the code tries to unpack a `rating` variable:

```python
[quality, quantity] = rating
```

However, when `rating` is `None` (which happens for meals without ratings, or past meals), it throws a `TypeError`.

### Impact on Our App

1. **Past Lunches Don't Load** ❌  
   When navigating to past dates (yesterday, last week, etc.), the API throws this error and our backend catches it, returning an empty list. Users see "No lunches served on this day" even if lunches existed.

2. **Ordered Status Not Showing** ❌  
   The API fails before it can parse which meal was ordered, so our app can't show if you've already ordered a lunch for a specific day.

### Working Features ✅

Despite this bug, the following features **DO work**:

- ✅ **Login** - Authentication works fine
- ✅ **Viewing Today's Lunches** - Often works (if meals don't have ratings causing the bug)
- ✅ **Viewing Future Lunches** - Sometimes works
- ✅ **Ordering Lunches** - Order/cancel functionality works when the meal list loads
- ✅ **Rating System** - Our custom rating system works independently
- ✅ **Photo Uploads** - Photo system works independently
- ✅ **UI/UX** - All frontend features work perfectly

### When It Fails

The bug is triggered when:
- Accessing past meals (which may have been rated on Edupage)
- Accessing meals without full rating data  
- The Edupage backend doesn't return rating data in the expected format

### Attempts to Fix

1. ✅ Updated to latest version (0.12.3) - still has the bug
2. ✅ Added try/catch error handling in our code - prevents crashes but can't load data
3. ❌ Can't monkeypatch the library easily without modifying installed package

### Solutions

#### Option 1: Wait for Library Fix (Recommended)
The best solution is to report this bug to the `edupage-api` maintainers and wait for a fix:

**Repository:** https://github.com/EdupageAPI/edupage-api  
**Issue to create:** "TypeError in parse_meal when rating is None"

#### Option 2: Fork and Fix
Fork the library, fix line 178, and install from the fork:

```python
# In edupage_api/lunches.py, line ~178
# Change from:
[quality, quantity] = rating

# To:
if rating:
    [quality, quantity] = rating
else:
    quality = None
    quantity = None
```

Then install from the fork:
```bash
pip install git+https://github.com/YOUR_USERNAME/edupage-api.git@fixed-rating-bug
```

#### Option 3: Local Patch (Quick Fix)
Directly edit the installed package (NOT RECOMMENDED for production):

```bash
# Find the file
find backend/venv -name "lunches.py" -path "*/edupage_api/*"

# Edit line 178 to add None check
nano backend/venv/lib/python3.13/site-packages/edupage_api/lunches.py
```

### Temporary Workaround

For now, the app works best with:
- **Today's lunches** - Primary use case
- **Future lunches** - Meal planning
- Avoid navigating to past dates until the bug is fixed

---

## Other Known Limitations

### 1. Session Persistence
- Sessions can expire
- Solution: Log out and log in again if you get auth errors

### 2. Weekend Navigation
- The app skips weekends, which is correct for most schools
- No lunches served on Saturdays/Sundays

### 3. Timezone
- Date comparisons use local device timezone
- Could cause issues for users in different timezones

---

## What This Means for Users

### ✅ What Works
- Order lunch for today ✅
- Order lunch for tomorrow ✅  
- View this week's menu ✅
- Cancel orders ✅
- Rate meals (using our custom system) ✅
- Upload photos ✅
- Navigate dates (clicking arrows) ✅

### ❌ What Doesn't Work
- Viewing past lunches (yesterday, last week) ❌
- Seeing if you already ordered for a day ❌
- Accessing historical meal data ❌

---

## Testing the Bug

To verify the bug yourself:

1. Login to the app
2. Navigate to yesterday's date
3. Check backend logs: `tail -f backend.log`
4. You'll see the `TypeError: cannot unpack non-iterable NoneType object`

---

## Conclusion

This is **not a bug in our code** - it's a bug in the `edupage-api` library itself. Our code is properly handling the error (catching exceptions and returning empty lists), but we can't access the data until the library is fixed.

**Recommendation:** Report this issue to the edupage-api GitHub repository and either wait for a fix or implement Option 2 (fork and fix).

---

## Links

- **Edupage-API Repository:** https://github.com/EdupageAPI/edupage-api
- **Documentation:** https://edupageapi.github.io/edupage-api/
- **PyPI Package:** https://pypi.org/project/edupage-api/
