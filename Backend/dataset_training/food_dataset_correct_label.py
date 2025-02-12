import os

labels_path = 'datasets/food41_yolo/labels/train'

def correct_label_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    corrected_lines = []
    for line in lines:
        # Remove 'True', 'False', '[' and ']'
        line = line.replace('True', '').replace('False', '').replace('[', '').replace(']', '').strip()
        corrected_lines.append(line + '\n')

    with open(file_path, 'w') as f:
        f.writelines(corrected_lines)

for label_file in os.listdir(labels_path):
    file_path = os.path.join(labels_path, label_file)
    correct_label_file(file_path)

print("Label files corrected.")