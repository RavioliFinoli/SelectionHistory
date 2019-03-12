# Animation Transfer Tool for Maya
A tool that transfers animation from one skeleton to another.

## Notes
  * Tracks selection of all object types. A filtering feature is planned.
  * The window is dockable for convenience.
  * Tested only on Autodesk Maya 2018.

<a name="installation"/>

## Installation
  * Copy SelectionHistory.py and selection_history.ui to your maya scripts folder (../Documents/maya/VERSION/scripts on Windows)
  * Create a python script in Maya with the following:
   ```python
   import SelectionHistory
   reload(SelectionHistory)
   SelectionHistory.run()
   ```
  * Run that script to open the tool (you can save this script to a shelf by selecting the code and dragging it onto a shelf and selecting 'Python' in the dialogue that pops up).
