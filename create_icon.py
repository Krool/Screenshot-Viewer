from PIL import Image, ImageDraw

def create_icon():
    # Create a new image with a transparent background
    size = (256, 256)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a rounded rectangle for the base
    bg_color = (27, 40, 56, 255)  # Steam dark blue
    draw.rounded_rectangle([(20, 20), (236, 236)], radius=30, fill=bg_color)
    
    # Draw a camera icon
    accent_color = (102, 192, 244, 255)  # Steam light blue
    # Camera body
    draw.rounded_rectangle([(68, 88), (188, 168)], radius=10, fill=accent_color)
    # Camera lens
    draw.ellipse([(98, 98), (158, 158)], fill=bg_color)
    draw.ellipse([(108, 108), (148, 148)], fill=accent_color)
    # Flash
    draw.rounded_rectangle([(158, 78), (178, 88)], radius=3, fill=accent_color)
    
    # Save in different sizes
    sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    image.save('app_icon.ico', format='ICO', sizes=sizes)

if __name__ == '__main__':
    create_icon() 