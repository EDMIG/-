import tkinter as tk
import tkinter.messagebox as tm
from PIL import Image, ImageTk, ImageDraw
import os
import json
import math
import copy

class LabelClass:
    def __init__(self):
        self.NNkeypoints=[[67.0, 17.0, 2], [13.0, 48.0, 2], [-28.0, 86.0, 2], \
                          [-60.0, 155.0, 2], [130.0, 45.0, 2], [196.0, 91.0, 2], [217.0, 159.0, 2], \
                          [41.0, 125.0, 2], [37.0, 215.0, 2], [33.0, 311.0, 2], [130.0, 120.0, 2], \
                          [126.0, 213.0, 2], [124.0, 312.0, 2], [40.0, -14.0, 2], [94.0, -18.0, 2], \
                          [-19.0, -30.0, 2], [144.0, -39.0, 2]] # 存储标准关节点
        self.Point =[] #标准骨架节点坐标
        self.Vector =[] #存储self.len的所有值
        self.VectorY =[] #存储self.len
        self.x =None #x坐标间距
        self.y =None #y坐标间距
        self.len =None #两关节点间距离
        self.strVar =None #Text文本显示
        self.kk =[] #存储与某点连接的所有线段
        self.jud =None
        self.judbool =False
        self.LeftClickCount =0 #连续左击次数
        '''
        self.dict={'0':'鼻子','1':'脖子','2':'右肩','3':'右手肘','4':'右手腕','5':'左肩','6':'左手肘',\
                   '7':'左手腕','8':'右胯','9':'右膝','10':'右脚','8':'右胯','9':'右膝','10':'右脚',\
                   '11':'左胯','12':'左膝','13':'左脚','14':'右眼','15':'左眼','16':'右耳','17':'左耳'}
        '''
        self.list=['鼻子','右肩','右手肘','右手腕','左肩','左手肘','左手腕','右胯','右膝','右脚踝',\
                   '左胯','左膝','左脚踝','右眼','左眼','右耳','左耳']
        self.keypoints = [] # 存储新关节点
        self.old_keypoints = None # OpenPose关节点
        self.size = None # 图片尺寸
        self.radius = 4 # 标记半径
        self.json_data = None # json格式数据
        self.reLable = False # 标记是否需要修改
        self.reLable1 = False
        self.index = None
        self.preindex=None
        self.VV=[] #储存新改过的线段及顶点索引，用以判断下个索引与此个索引是否有关联，并删除相关联的线段
        self.vvvv=[] #存储所有画过的新线段及对应顶点索引
        # openpose数据选择
        self.keyIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        # 关节点颜色
        self.color = ['blue', 'aqua', 'darkred', 'springgreen','yellow','red','fuchsia','grey', 'cyan', \
                      'brown', 'green', 'snow', 'salmon', 'tan', 'teal', 'tomato', 'yellowgreen']
          
        self.lineIndex = [[2, 3], [3, 4], [5, 6], [6, 7], [8, 9], \
           [9, 10], [11, 12], [12, 13], [1, 14], [14, 16], \
           [1, 15], [15, 17]]
          
        self.image_file = None

        # 主窗口
        self.window = tk.Tk()
        self.window.title('pyLable')
        self.window.geometry('1000x600')
        self.window.resizable(0, 0)
        self.canvas = None
        self.oval = [None for i in range(17)]  #画的点的索引
        self.ovalline = [None for i in range(12)]
        self.ovallineold = [None for i in range(12)]

        # 添加提示文本
        self.strVar=tk.Text(self.window,height=1,width=30)
        self.strVar.pack(side='top')
        
        #创建画布
        self.createCanvas()
        
        # 创建按键
        self.createButton()

        # 首先读取进度，并画出图形与关节点
        with open('pyRecord.txt', 'r') as f:  #打开文件
            lines = f.readlines() #读取所有行
            self.imgId = lines[-1] #取最后一行
            
        self.NNcanvas.create_image(250, 250)
        self.NNDrawPoints()
        
        self.tryDraw()
        self.DrawPoints()
        
        # 窗体循环
        self.window.mainloop()

        # 关闭则保存进度
        with open('pyRecord.txt', 'a+') as f: # 打开文件
            f.write('\n')
            f.write(str(int(self.imgId)-1))

    # 创建画布并添加鼠标监听
    def createCanvas(self):
        self.canvas = tk.Canvas(self.window, bg='black', height=500, width=500)
        self.canvas.pack(side='left')
        self.canvas.bind('<Button-1>', self.LClick) # 左画布监听左键
        self.canvas.bind('<Button-3>', self.RClick) # 左画布监听右键
        
        self.NNcanvas = tk.Canvas(self.window, bg='black', height=500, width=500)
        self.NNcanvas.pack()
        self.NNcanvas.bind('<Button-1>', self.leftClick) # 右画布监听左键
        self.NNcanvas.bind('<Button-3>', self.rightClick) # 右画布监听右键
    
    # 创建按键
    def createButton(self):
        b = tk.Button(self.window, 
            text='写入',
            width=30, height=2, 
            command=self.writeRes)
        b.pack(side = 'left') 

        b = tk.Button(self.window, 
            text='返回',
            width=30, height=2, 
            command=self.last)
        b.pack(side = 'left')
        
    # 左画布鼠标左键响应
    def LClick(self, event):
        self.LeftClickCount+=1
        if self.reLable:
            # 上次记录清空
            self.keypoints[self.index]=[]
            self.canvas.delete(self.oval[self.index])
            for vv in self.vvvv:
                for indt in vv:
                    if self.index==indt[0] or self.index==indt[1]:
                        for ii in range(12):
                            if indt[2]==self.ovalline[ii]:
                                self.canvas.delete(self.ovalline[ii])
            if self.judbool or self.LeftClickCount >1:
                for ind in self.kk:
                    self.canvas.delete(self.ovalline[ind])
            else:
                for indt in self.VV:
                    if [self.preindex,self.index] == [indt[0],indt[1]] or [self.index,self.preindex] == [indt[0],indt[1]]:
                        for ii in range(12):
                            if indt[2]==self.ovalline[ii]:
                                self.canvas.delete(self.ovalline[ii])

            self.VV=[]
            self.preindex=self.index
            self.judbool =False    
            self.kk=[]

            # 画点
            self.oval[self.index] = self.canvas.create_oval(event.x-self.radius,
                event.y-self.radius,
                event.x+self.radius,
                event.y+self.radius, 
                fill=self.color[self.index])
            
            # 存储坐标点
            self.keypoints[self.index]=(event.x-250+self.size[0]/2, 
                event.y-250+self.size[1]/2, 2)
            
            #画线
            point0 = self.keypoints[self.index]
            for k in range(len(self.lineIndex)):
                if self.index==self.lineIndex[k][0]-1:
                    indexB = self.lineIndex[k][1]-1
                    point1 = self.keypoints[indexB]
                    if point0[2] and point1[2]:
                        
                        self.ovalline[k]=self.canvas.create_line(int(250-self.size[0]/2+point0[0]),int(250-self.size[1]/2+point0[1]),\
                                            int(250-self.size[0]/2+point1[0]),int(250-self.size[1]/2+point1[1]),fill='red')
                        self.canvas.delete(self.ovallineold[k])
                        self.kk.append(k)
                        self.VV.append([self.index,indexB,self.ovalline[k]])
                        self.vvvv.append(self.VV)
                if self.index==self.lineIndex[k][1]-1:
                    indexB = self.lineIndex[k][0]-1
                    point1 = self.keypoints[indexB]
                    if point0[2] and point1[2]:

                        self.ovalline[k]=self.canvas.create_line(int(250-self.size[0]/2+point0[0]),int(250-self.size[1]/2+point0[1]),\
                                            int(250-self.size[0]/2+point1[0]),int(250-self.size[1]/2+point1[1]),fill='red')
                        self.canvas.delete(self.ovallineold[k])
                        self.kk.append(k)
                        self.VV.append([indexB,self.index,self.ovalline[k]])
                        self.vvvv.append(self.VV)
    # 左画布鼠标右键响应
    def RClick(self,event):
        if self.reLable1:
            self.keypoints[self.index]=[0,0,0]
            self.canvas.delete(self.oval[self.index])
            for indt in self.VV:
                if self.index == indt[0] or self.index == indt[1]:
                    for ii in range(12):
                        if indt[2]==self.ovalline[ii]:
                            self.canvas.delete(self.ovalline[ii])
            for tt in range(len(self.lineIndex)):
                if self.index==self.lineIndex[tt][0]-1 or self.index==self.lineIndex[tt][1]-1:
                    if self.ovalline[tt]:
                        self.canvas.delete(self.ovalline[tt])
            for jj in range(len(self.lineIndex)):
                if self.index==self.lineIndex[jj][0]-1 or self.index==self.lineIndex[jj][1]-1:
                    if self.ovallineold[jj]:
                        self.canvas.delete(self.ovallineold[jj])
    
    #右画布左键响应
    def leftClick(self, event):
        self.reLable1 = False
        self.LeftClickCount=0
        self.Vector=[]
        self.strVar.delete('1.0','end')
        self.Point=(event.x-250+84, event.y-250+156, 2)
        #print(self.Point)
        #print(self.keypoints)
        for ind in range(17):
            self.lenth(self.NNkeypoints[ind])
            self.Vector.append(self.len)
            
        #print(self.Vector)
        self.index=self.Vector.index(min(self.Vector))
        
        
        self.reLable = True
        self.strVar.insert('end', '您要修改的是'+self.list[self.index]+'  id is '+str(self.index))
        if self.jud ==self.index:
            self.judbool=True
        self.jud=self.index
        #print(self.index)

    #右画布右键响应
    def rightClick(self,event):
        self.reLable = False
        #self.LeftClickCount=0
        self.VectorY=[]
        self.strVar.delete('1.0','end')
        self.Point=(event.x-250+84, event.y-250+156, 2)
        #print(self.Point)
        #print(self.keypoints)
        for ind in range(17):
            self.lenth(self.NNkeypoints[ind])
            self.VectorY.append(self.len)
            
        #print(self.Vector)
        self.index=self.VectorY.index(min(self.VectorY))
        
        
        self.reLable1 = True
        self.strVar.insert('end', '您要清除的是'+self.list[self.index]+'  id is '+str(self.index))
        '''
        if self.jud ==self.index:
            self.judbool=True
        self.jud=self.index
        '''
        #print(self.index)
    # 防止图片不存在
    def tryDraw(self):
        count = 0
        while True:
            if count > 100:
                tm.showinfo(title='警告',message='超过100个图片不存在，请确认pyRecord.txt文件是否正确')
                exit(0)
            count += 1
            self.imgId = str(int(self.imgId)+1).zfill(6)
            try:
                self.drawImg()
            except Exception as e:
                print(e)
            else:
                break

    # 画出图形
    def drawImg(self):
        filepath = os.path.abspath(os.curdir) + '/bodyImg/' + self.imgId + '.bmp'
        imgName = Image.open(filepath) # tk不支持bmp，使用PIL转化
        self.size = imgName.size
        self.image_file = ImageTk.PhotoImage(image=imgName) 
        self.image = self.canvas.create_image(250, 250, image=self.image_file)
        
    # 画出关节点
    def NNDrawPoints(self):
        
        # 画出关节点
        for ind in range(len(self.NNkeypoints)):
            point = self.NNkeypoints[ind]
            if point[2]:
                self.NNcanvas.create_oval(
                    250-84+point[0]-5,
                    250-156+point[1]-5,
                    250-84+point[0]+5,
                    250-156+point[1]+5, 
                    fill=self.color[ind])
                
        # 画出关节点之间的连线 
        for k in range(len(self.lineIndex)):
            indexA = self.lineIndex[k][0]-1
            indexB = self.lineIndex[k][1]-1
            point0 = self.NNkeypoints[indexA]
            point1 = self.NNkeypoints[indexB]
            if point0[2] and point1[2]:

                self.NNcanvas.create_line(int(250-84+point0[0]),int(250-156+point0[1]),\
                                            int(250-84+point1[0]),int(250-156+point1[1]),fill='yellow')
                
                
    def DrawPoints(self):
        # 读取OpenPose的json格式数据并解析选择
        filepath = os.path.abspath(os.curdir) + '/output/' + self.imgId + '_keypoints.json'
        with open(filepath, encoding='utf-8') as f:
            self.json_data = json.load(f)
            if len(self.json_data['people']):
                keypoints = self.json_data['people'][0]['pose_keypoints_2d']
                for ind in range(18):
                    if ind !=1:
                        self.keypoints.append((keypoints[ind*3], keypoints[ind*3+1], keypoints[ind*3+2]))
        #print(len(self.keypoints))
        if self.keypoints==[]:
            for i in range(17):
                self.keypoints.append([0,0,0])            
        # 保存旧的OpenPose关节点
        self.old_keypoints = copy.deepcopy(self.keypoints)
        
        '''
        print(self.imgId+'帧旧的json点')
        print(self.keypoints)
        '''
        print(self.imgId+'帧开始')
        
        # 画出关节点
        for ind in range(len(self.keypoints)):
            point = self.keypoints[ind]
            if point[2]:
                self.oval[ind] = self.canvas.create_oval(
                    250-self.size[0]/2+point[0]-self.radius,
                    250-self.size[1]/2+point[1]-self.radius,
                    250-self.size[0]/2+point[0]+self.radius,
                    250-self.size[1]/2+point[1]+self.radius, 
                    fill=self.color[ind])
                
        # 画出关节点之间的连线 
        for k in range(len(self.lineIndex)):
            indexA = self.lineIndex[k][0]-1
            indexB = self.lineIndex[k][1]-1
            point0 = self.keypoints[indexA]
            point1 = self.keypoints[indexB]
            if point0[2] and point1[2]:

                self.ovallineold[k] =self.canvas.create_line(int(250-self.size[0]/2+point0[0]),int(250-self.size[1]/2+point0[1]),\
                                            int(250-self.size[0]/2+point1[0]),int(250-self.size[1]/2+point1[1]),fill='yellow')
    
    # 保存图片
    def savaImage(self):
        oimage = os.path.abspath(os.curdir) + '/bodyImg/' + self.imgId + '.bmp'
        rimage = os.path.abspath(os.curdir) + '/resImg/' + self.imgId + '.bmp'
        im = Image.open(oimage)
        ################################li
        org_width, org_height = im.size
        a=int(org_width/2)
        b=int(org_height/2)
        mode = im.mode

        newImage = Image.new(mode, (500, 500))
        add_im1 = Image.new(mode, (500, 250-b), (0,0,0))
        add_im2 = Image.new(mode, (250-a, org_height), (0,0,0))
        newImage.paste(im, (250-a, 250-b, 250-a+ org_width, 250-b+org_height))
        newImage.paste(add_im1, (0, 0, 500, 250-b))
        newImage.paste(add_im1, (0, 250+b, 500, 500))
        newImage.paste(add_im2, (0, 250-b, 250-a, 250-b+org_height))
        newImage.paste(add_im2, (250+a, 250-b, 500, 250-b+org_height))
        new=copy.deepcopy(newImage)
        ################################li
        draw = ImageDraw.Draw(new)
        for ind in range(len(self.keypoints)):
                point = self.keypoints[ind]
                if point[2]:
                    draw.ellipse((point[0]-self.radius+250-a, 
                        point[1]-self.radius+250-b, 
                        point[0]+self.radius+250-a, 
                        point[1]+self.radius+250-b), fill=self.color[ind])
        # 画出关节点之间的连线 
        for k in range(len(self.lineIndex)):
            indexA = self.lineIndex[k][0]-1
            indexB = self.lineIndex[k][1]-1
            point0 = self.keypoints[indexA]
            point1 = self.keypoints[indexB]
            if point0[2] and point1[2]:

                draw.line((int(250-self.size[0]/2+point0[0]),int(250-self.size[1]/2+point0[1]),\
                                            int(250-self.size[0]/2+point1[0]),int(250-self.size[1]/2+point1[1])),fill=128)
        # 保存结果图片
        new.save(rimage)

        # 如果发生变化，保存变化前后图片
        if self.reLable or self.reLable1:
            filepath_new = os.path.abspath(os.curdir) + '/reLableStatus/' + self.imgId + '_new.bmp'
            new.save(filepath_new)
            #newImage = Image.open(oimage)
            draw = ImageDraw.Draw(newImage)
            for ind in range(len(self.old_keypoints)):
                    point = self.old_keypoints[ind]
                    if point[2]:
                        draw.ellipse((point[0]-self.radius+250-a, 
                            point[1]-self.radius+250-b, 
                            point[0]+self.radius+250-a, 
                            point[1]+self.radius+250-b), fill=self.color[ind])
            # 画出关节点之间的连线 
            for k in range(len(self.lineIndex)):
                indexA = self.lineIndex[k][0]-1
                indexB = self.lineIndex[k][1]-1
                point0 = self.old_keypoints[indexA]
                point1 = self.old_keypoints[indexB]
                if point0[2] and point1[2]:
    
                    draw.line((int(250-self.size[0]/2+point0[0]),int(250-self.size[1]/2+point0[1]),\
                                                int(250-self.size[0]/2+point1[0]),int(250-self.size[1]/2+point1[1])),fill=128)
                
            filepath_old = os.path.abspath(os.curdir) + '/reLableStatus/' + self.imgId + '_old.bmp'
            #print(self.old_keypoints)
            newImage.save(filepath_old)
            
    # 计算两点距离
    def lenth(self, a):
        self.x=self.Point[0]-a[0]
        self.y=self.Point[1]-a[1]
        self.len =math.sqrt(self.x**2+self.y**2)
      
        
    # 清除画布上的关节点
    def destroyPoints(self):
        for o in range(17):
            if self.oval[o]:
                self.canvas.delete(self.oval[o])
                self.oval[o] = None

    # 清除画布上的所有线段
    def destoryLine(self):
        # 清除新的线段
        for vv in self.vvvv:
            for indt in vv:
                for ii in range(12):
                    if indt[2]==self.ovalline[ii]:
                        self.canvas.delete(self.ovalline[ii])
        # 清除旧的线段
        for k in range(len(self.lineIndex)):
            self.canvas.delete(self.ovallineold[k])
    # 写入数据
    def writeRes(self):
        # 标记数量不足，弹窗警告
        
        if len(self.keypoints) < 17:
            tm.showinfo(title='警告',message='标记点数不足')
            return

        # openpose未检测到人体特殊处理
        if len(self.json_data['people']) == 0:
            self.json_data['people'].append({})

        # 存储json格式数据
        self.json_data['people'][0]['pose_keypoints_2d'] = self.keypoints
        self.json_data['people'][0]['size'] = self.size
        filepath = os.path.abspath(os.curdir) + '/json_data/' + self.imgId + '_keypoints.json'
        with open(filepath, 'w+') as f:
            json.dump(self.json_data, f)
        self.savaImage()
        
        #print('新改写的json点')
        #print(self.keypoints)
        print(self.imgId +'帧结束')
        print(' ')

        # 重置各变量
        self.keypoints = []
        self.size = None
        self.reLable = False
        self.reLable1 =False
        self.strVar.delete('1.0','end')
        # 清除节点
        self.destroyPoints()
        # 清除连线
        self.destoryLine()
        # 重新画图
        self.tryDraw()
        self.DrawPoints()
        
    # 返回上一张图片
    def last(self):
        self.imgId = str(int(self.imgId)-1).zfill(6)
        self.clear()
        self.DrawPoints()
        self.reLable = False
        self.reLable1 =False
    
    # 清除关节点和连线
    def clear(self):
        self.keypoints = []
        self.size = None
        self.destroyPoints()
        self.destoryLine()
        # 重画覆盖
        self.drawImg()
        
print('start!')
LabelClass()
print('done!')