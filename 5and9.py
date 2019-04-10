import tkinter as tk
import tkinter.messagebox as tm
from PIL import Image, ImageTk, ImageDraw
import os
import json
import math
import copy
import re

class LabelClass:
    def __init__(self):
        self.NNkeypoints=[[68.0, 46.0, 2], [13.0, 48.0, 2], [130.0, 45.0, 2], [41.0, 125.0, 2], [37.0, 215.0, 2], [33.0, 311.0, 2], [130.0, 120.0, 2], \
                          [126.0, 213.0, 2], [124.0, 312.0, 2]] # 存储标准关节点
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
        self.list=['脖子','右肩', '左肩', '右胯','右膝','右脚踝','左胯','左膝','左脚踝']
        self.aa=[]
        self.keypoints = [] # 存储新关节点
        self.old_keypoints = None # OpenPose关节点
        self.size = None # 图片尺寸
        self.radius = 4 # 标记半径
        self.json_data = None # json格式数据
        self.json_data1 = None
        self.reLable = False # 标记是否需要修改
        self.reLable1 = False
        self.index = None
        self.preindex=None
        self.VV=[] #储存新改过的线段及顶点索引，用以判断下个索引与此个索引是否有关联，并删除相关联的线段
        self.vvvv=[] #存储所有画过的新线段及对应顶点索引
        # openpose数据选择
        self.keyIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        # 关节点颜色
        self.color = ['aqua', 'darkred', 'red', 'darkmagenta', \
                      'deeppink', 'green', 'dimgray', 'snow', 'salmon']
        self.lineIndex = [[1, 2], [1, 3], [4, 5], [5, 6], [7, 8], [8, 9]]
          
        self.image_file = None

        # 主窗口
        self.window = tk.Tk()
        self.window.title('pyLable')
        self.window.geometry('1000x600')
        self.window.resizable(0, 0)
        self.canvas = None
        self.oval = [None for i in range(9)]  #画的点的索引
        self.ovalline = [None for i in range(6)]
        self.ovallineold = [None for i in range(6)]

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
                        for ii in range(6):
                            if indt[2]==self.ovalline[ii]:
                                self.canvas.delete(self.ovalline[ii])
            if self.judbool or self.LeftClickCount >1:
                for ind in self.kk:
                    self.canvas.delete(self.ovalline[ind])
            else:
                for indt in self.VV:
                    if [self.preindex,self.index] == [indt[0],indt[1]] or [self.index,self.preindex] == [indt[0],indt[1]]:
                        for ii in range(6):
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
            
            if self.keypoints[self.index][0]>self.size[0] or self.keypoints[self.index][1]>self.size[1] or self.keypoints[self.index][0]< 0 or self.keypoints[self.index][1]<0:
                tm.showinfo(title='警告',message='超出分辨率，请重新修改')
                return
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
                    for ii in range(6):
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
        for ind in range(9):
            self.lenth(self.NNkeypoints[ind])
            self.Vector.append(self.len)
            
        #print(self.Vector)
        self.index=self.Vector.index(min(self.Vector))
        
        
        self.reLable = True
        self.strVar.insert('end', '您要修改的是'+self.list[self.index]+'  id is '+str(self.index))
        self.judbool =False
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
        for ind in range(9):
            self.lenth(self.NNkeypoints[ind])
            self.VectorY.append(self.len)
            
        #print(self.Vector)
        self.index=self.VectorY.index(min(self.VectorY))
        
        
        self.reLable1 = True
        self.strVar.insert('end', '您要清除的是'+self.list[self.index]+'  id is '+str(self.index))
       
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
                    if ind==1 or ind==2 or ind== 5:
                        self.keypoints.append((keypoints[ind*3], keypoints[ind*3+1], keypoints[ind*3+2]))
                    if ind >7 and ind <14:
                        self.keypoints.append((keypoints[ind*3], keypoints[ind*3+1], keypoints[ind*3+2]))
        #print(len(self.keypoints))
        if self.keypoints==[]:
            for i in range(9):
                self.keypoints.append([0,0,0])            
        # 保存旧的OpenPose关节点
        self.old_keypoints = copy.deepcopy(self.keypoints)
        
        
        filepath1 = os.path.abspath(os.curdir) + '/json_data/' + self.imgId + '_keypoints.json'
        if os.path.isfile(filepath1):
            self.json_data = None
            self.keypoints = []
            with open(filepath1, encoding='utf-8') as f:
                self.json_data = json.load(f)
                if len(self.json_data['people']):
                    keypoints = self.json_data['people'][0]['pose_keypoints_2d']
                    for ind in range(14):
                        if ind ==1 or ind ==2 or ind ==5 or ind >7:
                            self.keypoints.append(keypoints[ind])
            if self.keypoints==[]:
                for i in range(9):
                    self.keypoints.append([0,0,0])
                    
                    
        
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
        draw = ImageDraw.Draw(im)
        for ind in range(len(self.keypoints)):
                point = self.keypoints[ind]
                if point[2]:
                    draw.ellipse((point[0]-self.radius, 
                        point[1]-self.radius, 
                        point[0]+self.radius, 
                        point[1]+self.radius), fill=self.color[ind])
         # 画出关节点之间的连线 
        for k in range(len(self.lineIndex)):
            indexA = self.lineIndex[k][0]-1
            indexB = self.lineIndex[k][1]-1
            point0 = self.keypoints[indexA]
            point1 = self.keypoints[indexB]
            if point0[2] and point1[2]:

                draw.line((int(point0[0]),int(point0[1]),\
                                            int(point1[0]),int(point1[1])),fill=128)
        # 保存结果图片
        im.save(rimage)

        # 如果发生变化，保存变化前后图片
        if self.reLable or self.reLable1:
            filepath_new = os.path.abspath(os.curdir) + '/reLableStatus/' + self.imgId + '_new.bmp'
            im.save(filepath_new)
            im = Image.open(oimage)
            draw = ImageDraw.Draw(im)
            for ind in range(len(self.old_keypoints)):
                    point = self.old_keypoints[ind]
                    if point[2]:
                        draw.ellipse((point[0]-self.radius, 
                            point[1]-self.radius, 
                            point[0]+self.radius, 
                            point[1]+self.radius), fill=self.color[ind])
             # 画出关节点之间的连线 
            for k in range(len(self.lineIndex)):
                indexA = self.lineIndex[k][0]-1
                indexB = self.lineIndex[k][1]-1
                point0 = self.old_keypoints[indexA]
                point1 = self.old_keypoints[indexB]
                if point0[2] and point1[2]:
    
                    draw.line((int(point0[0]),int(point0[1]),\
                                                int(point1[0]),int(point1[1])),fill=128)
            filepath_old = os.path.abspath(os.curdir) + '/reLableStatus/' + self.imgId + '_old.bmp'
            #print(self.old_keypoints)
            im.save(filepath_old)
            
    # 计算两点距离
    def lenth(self, a):
        self.x=self.Point[0]-a[0]
        self.y=self.Point[1]-a[1]
        self.len =math.sqrt(self.x**2+self.y**2)
      
        
    # 清除画布上的关节点
    def destroyPoints(self):
        for o in range(9):
            if self.oval[o]:
                self.canvas.delete(self.oval[o])
                self.oval[o] = None

    # 清除画布上的所有线段
    def destoryLine(self):
        # 清除新的线段
        for vv in self.vvvv:
            for indt in vv:
                for ii in range(6):
                    if indt[2]==self.ovalline[ii]:
                        self.canvas.delete(self.ovalline[ii])
        # 清除旧的线段
        for k in range(len(self.lineIndex)):
            self.canvas.delete(self.ovallineold[k])
    # 写入数据
    def writeRes(self):
        # 标记数量不足，弹窗警告
        
        if len(self.keypoints) < 9:
            tm.showinfo(title='警告',message='标记点数不足')
            return
        for fd in range(9):
            if self.keypoints[fd][0]>self.size[0] or self.keypoints[fd][1]>self.size[1] or self.keypoints[fd][0]< 0 or self.keypoints[fd][1]<0:
                tm.showinfo(title='警告',message='有点超出分辨率，请检查')
                return
        # openpose未检测到人体特殊处理
        if len(self.json_data['people']) == 0:
            self.json_data['people'].append({})

            
        filepath = os.path.abspath(os.curdir) + '/labeled/' + 'new_keypoints_train.txt'
        for line in open(filepath):
            line1=re.split(' ',line)

            self.json_data1='000000'+self.imgId
            if line[0:12]==self.json_data1:
                for ind in range(7):
                    if ind !=1 and ind !=4:
                    #print((int(line1[ind*3+1]), int(line1[ind*3+2]), int(line1[ind*3+3])))
                        self.aa.append((int(line1[ind*3+1]), int(line1[ind*3+2]), int(line1[ind*3+3])))
                break
   
        # 存储json格式数据
        self.json_data['people'][0]['pose_keypoints_2d'] =[self.aa[0]] + self.keypoints[0:2]+self.aa[1:3]+[self.keypoints[2]]+self.aa[3:]+self.keypoints[3:]
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
        self.aa=[]
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