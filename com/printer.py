import win32print, win32ui, tempfile, win32api
from PIL import Image, ImageWin
import os
from flask import current_app
from openpyxl.drawing.image import Image
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
def insert_print_data(asset, print_bar):
    # 写入数据
    import openpyxl
    work_book = openpyxl.load_workbook(print_bar)
    work_sheet = work_book.active
    # 资产信息
    work_sheet['B2'] = asset.sap_code
    work_sheet['D2'] = asset.buy_date.strftime('%Y-%m-%d')
    work_sheet['B3'] = asset.class3.name
    work_sheet['D3'] = asset.code
    work_sheet['B4'] = '{} - {}'.format(asset.brand.name, asset.model.name)
    # 条码
    bar_path = current_app.config['BAR_CODE_PATH'] + '\\' + asset.bar_path
    if os.path.exists(bar_path):
        bar_img = Image(bar_path)
        bar_img.width, bar_img.height = (270, 35)
        p2e = pixels_to_EMU
        size = XDRPositiveSize2D(p2e(bar_img.width), p2e(bar_img.height))
        marker = AnchorMarker(col=0, colOff=75000, row=5, rowOff=45000)
        # bar_img.anchor = 'A6'
        bar_img.anchor = OneCellAnchor(_from=marker, ext=size)
        work_sheet.add_image(bar_img)
    else:
        print('bar image is not exist!')
    # 保存
    work_book.save(print_bar)
def gen_pdf(asset):
    file_name = os.path.join(os.path.join(current_app.config['FILE_UPLOAD_PATH'], 'temp'), asset.code + '.pdf')
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle, Paragraph
    pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))     # 注册字体-务必将SimSun.ttf字体文件放到对应的包里，路径：site-packages\reportlab\fonts
    elements = []
    bar_path = current_app.config['BAR_CODE_PATH'] + '\\' + asset.bar_path
    print(bar_path)
    i = Image(bar_path)
    i.drawHeight = 0.8 * inch * i.drawHeight / i.drawWidth
    i.drawWidth = 2.5 * inch
    data = [
        ['资产代码(SAP)', asset.sap_code, '采购日期', asset.buy_date.strftime('%Y-%m-%d')],
        ['资产名称', asset.class3.name, '资产编号', asset.code],
        ['型号', '{} - {}'.format(asset.brand.name, asset.model.name), '', ''],
        ['管理部门', 'DICI PI/IT', '数量', '1'],
        [i, '', '', ''],
        ['※  本装备由斗山(中国)投资有限公司所有移动及销毁请事先取得主管部门的许可  ※', '', '', '']
    ]
    t = Table(data, 5 * [1.3 * inch], 6 * [0.2 * inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),       # 字体
        ('FONTSIZE', (0, 0), (-1, -1), 8),              # 大小
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),  # 设定单元格
        ('SPAN', (1, 2), (-1, 2)),                      # 合并单元格，合并第三行
        ('SPAN', (0, 4), (-1, 4)),                      # 合并单元格，合并第五行
        ('SPAN', (0, 5), (-1, 5)),                      # 合并单元格，合并第六行
        ('ALIGN', (0, 4), (-1, 4), 'CENTER'),           # 设定倒数第二行为居中对齐
        ('ALIGN', (0, 5), (-1, 5), 'CENTER'),           # 设定最后一行为居中对齐
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),         # 设定垂直居中
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(t)
    doc = SimpleDocTemplate(file_name)
    doc.build(elements)
    return file_name
def print_asset_card(file):
    win32api.ShellExecute(0, 'print', file, '/d:"%s"' % win32print.GetDefaultPrinter(), '.', 0)
def simple_print():
    temp_file = tempfile.mktemp('.txt')
    open(temp_file, 'w').write('This is a test!!!')
    win32api.ShellExecute(0, 'printto', temp_file, '"%s"' % win32print.GetDefaultPrinter(), '.', 0)
def print_image(file_name):
    #
    # Constants for GetDeviceCaps
    #
    #
    # HORZRES / VERTRES = printable area
    #
    HORZRES = 8
    VERTRES = 10
    #
    # LOGPIXELS = dots per inch
    #
    LOGPIXELSX = 88
    LOGPIXELSY = 90
    #
    # PHYSICALWIDTH/HEIGHT = total area
    #
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
    #
    # PHYSICALOFFSETX/Y = left / top margin
    #
    PHYSICALOFFSETX = 112
    PHYSICALOFFSETY = 113
    printer_name = win32print.GetDefaultPrinter()
    #
    # You can only write a Device-independent bitmap
    #  directly to a Windows device context; therefore
    #  we need (for ease) to use the Python Imaging
    #  Library to manipulate the image.
    #
    # Create a device context from a named printer
    #  and assess the printable size of the paper.
    #
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
    printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)
    #
    # Open the image, rotate it if it's wider than
    #  it is high, and work out how much to multiply
    #  each pixel by to get it as big as possible on
    #  the page without distorting.
    #
    bmp = Image.open(file_name)
    # if bmp.size[0] > bmp.size[1]:
    #     bmp = bmp.rotate(90)
    ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
    scale = min(ratios)
    #
    # Start the print job, and draw the bitmap to
    #  the printer device at the scaled size.
    #
    hDC.StartDoc(file_name)
    hDC.StartPage()
    dib = ImageWin.Dib(bmp)
    scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
    x1 = int((printer_size[0] - scaled_width) / 2)
    y1 = int((printer_size[1] - scaled_height) / 2)
    x2 = x1 + scaled_width
    y2 = y1 + scaled_height
    dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
def gen_html():
    pass
    # 生成HTML格式数据表格
    '''
    使用PrettyTable生成表格后再生成图片打印的方案放弃！
    原因：
        PrettyTable不能去除标题，不能合并单元格！！！
    '''
    """
    html = os.path.join(os.path.join(current_app.config['FILE_UPLOAD_PATH'], 'temp'), asset.code+'.html')
    content = '''
        <html>
            <body>        
                <table>          
                    <tr>
                      <td>资产代码(SAP)</td>
                      <td>1231321313</td>
                      <td>采购日期</td>
                      <td>2022-05-06</td>
                    </tr>
                    <tr>
                      <td>资产名称</td>
                      <td>笔记本电脑</td>
                      <td>资产编号</td>
                      <td>AS20220502001</td>
                    </tr>
                    <tr>
                      <td>型号</td>
                      <td colspan="3">惠普 - A002135</td>
                    </tr>
                    <tr>
                      <td>管理部门</td>
                      <td>DICI IT/PI</td>
                      <td>数量</td>
                      <td>1</td>
                    </tr>                    
               </table>  
            </body>
        <html>       
    '''
    with open(html, 'w') as f:
        f.write(content)
    # 生成PrettyTable表格
    from prettytable import from_html_one, PrettyTable, MSWORD_FRIENDLY, FRAME
    with open(html, "r") as f:
        html = f.read()
    table = from_html_one(html)
    # table = PrettyTable()
    table.header = False
    table.border = True
    table.preserve_internal_border = True
    table.hrules = FRAME
    table.set_style(MSWORD_FRIENDLY)
    table.align = "l"
    print('HTML type is : ', type(table.get_html_string()))
    print(table.get_html_string())
    # # 表格内容插入
    # table.add_row(['chal', '23', '中国', 'Shanghai'])
    # table.add_row(['charle', '29', 'China', 'Xuzhou'])
    # table.add_row(['jack', '32', 'United States', 'Washington'])
    space = 5
    # 生成表格图片
    from PIL import Image, ImageDraw, ImageFont
    # 字体
    font = ImageFont.truetype(font=r'C:\Windows\Fonts\simhei.ttf', encoding='utf-8')
    # Image模块创建一个图片对象
    im = Image.new('RGB', (10, 10), (0, 0, 0, 0))
    # ImageDraw向图片中进行操作，写入文字或者插入线条都可以
    draw = ImageDraw.Draw(im, "RGB")
    # 根据插入图片中的文字内容和字体信息，来确定图片的最终大小
    img_size = draw.multiline_textsize(str(table), font=font)
    # 图片初始化的大小为10-10，现在根据图片内容要重新设置图片的大小
    im_new = im.resize((img_size[0] + space * 2, img_size[1] + space * 2))
    del draw
    del im
    draw = ImageDraw.Draw(im_new, 'RGB')
    # 批量写入到图片中，这里的multiline_text会自动识别换行符
    draw.multiline_text((space, space), str(table), fill=(255, 255, 255), font=font)
    table_image_path = os.path.join(os.path.join(current_app.config['FILE_UPLOAD_PATH'], 'temp'), asset.code+'.png')
    im_new.save(table_image_path, "PNG")
    del draw
    print('File to print : ', table_image_path)
    """