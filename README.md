== packgerbs

Don't you wish your EDA tool would output release files for manufacture and assembly that fit exactly what your shop needs? Wouldn't it be nice if it could just combine the layers any one specific shop needed, and rename and package them as appropriate? Well, I do. So I made a script to do it for me.

Eventually I'd like to see this turn in to a full-blown gerber, drill file, and anything else merging script. It can already merge multiple gerber files into one layer (I use it for eg. Sierra Proto Express, who want a board outline on the top solder mask layer), and drills shouldn't be much harder to add. Even further along, I'd like to add in automated file submission, one-click ordering.

My first project using argparse, hopefully just running packgerbs.py will give enough info to get someone started.
