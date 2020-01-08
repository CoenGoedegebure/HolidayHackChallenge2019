# Bypassing the Frido Sleigh CAPTEHA

This is my solution for Objective 8 of the SANS Holiday Hack Challenge 2019.
You can read the writeup for Objective 8 on https://www.coengoedegebure.com

This is a bit of a Spartan script. It does have a neat progress bar, but no command line options to call the different stages.
Therefore, before you run it, there are a few things you should do in a sequence:
1) In the crack_capteha() method, change the value of the `email_address` variable to your own email address (line 168). This is the email address where you will receive the winning code
2) Extract the capteha_images.tar.gz to a directory and put the full directory path in the `capteha_images_path` variable in the main() method (line 220)
3) Uncomment the `initialize_training_set()` method call (line 224)
4) Uncomment the `train_model()` method call (line 227)
5) run frido.py. This prepares and trains the model
6) Comment lines 224 and 227 again
7) Uncomment the `crack_capteha()` method call (line 230) 
8) run frido.py


