from flask import Flask, request
import os
import subprocess
import datetime
import time
import json
import psutil
app = Flask(__name__)



@app.route('/')
def index():

    return '''
        <html>
            <head>
                <title>web直播推流工具</title>
                <link rel="stylesheet" href="//unpkg.com/element-ui@2.15.13/lib/theme-chalk/index.css">
                
            </head>
            <body>
                <script src="//unpkg.com/vue@2/dist/vue.js"></script>
                <script src="//unpkg.com/element-ui@2.15.13/lib/index.js"></script>
                <script src="//unpkg.com/axios/dist/axios.min.js"></script>
                <div id="app">
                <h2>web直播推流工具</h2>
                <el-form ref="formInline" :inline="true" :model="formInline" class="demo-form-inline">
                      <el-form-item label="回放视频：" prop="file" required>
                            <!--<el-input style="width: 500px" v-model="formInline.file" placeholder="点击选择文件" readonly @click.native="$refs.fileInput.click()"></el-input>-->
                            <el-input type="text" style="width: 500px" v-model="formInline.file" placeholder="视频文件/m3u8网址"></el-input>
                            <input type="file" ref="fileInput" style="display: none" @change="handleFile">
                            <el-button type="primary" @click="selectFile">选择文件</el-button>
                            </input>
                      </el-form-item>
                      <el-form-item label="推流密钥：" prop="key" required>
                        <el-input v-model="formInline.key" placeholder="推流密钥"></el-input>
                      </el-form-item> 
                      <el-form-item label="播放次数：">
                        <el-select v-model="formInline.times" style="width: 100px;">
                            <el-option v-for="n in 20" :key="n" :label="n" :value="n"></el-option>
                        </el-select>
                      </el-form-item>                   
                      <el-form-item>
                        <el-button type="primary" @click="openFullScreen1">开始推流</el-button>
                      </el-form-item>
                </el-form>             
                <hr/>
                <h2>当前推流任务列表</h2>
                <el-table :data="streamTasks" :default-sort="{prop: 'duration'}" style="width: 100%">
                  <el-table-column prop="file" label="回放视频" width="500"></el-table-column>
                  <el-table-column prop="pid" label="进程id"></el-table-column>
                  <el-table-column prop="times" label="播放次数"></el-table-column>
                  <el-table-column prop="status" label="状态"></el-table-column>
                  <el-table-column prop="duration" label="剩余播放时长"   align="center" width="120">
                      <template slot-scope="scope">
                        <el-statistic format="HH:mm:ss" :value="Date.now()+(scope.row.duration-(Date.now()-scope.row.start_time))" time-indices >
                      </template>
                  </el-table-column>
                  <el-table-column prop="start_time" label="开始时间" :formatter="row=>new Date(row.start_time).toLocaleString()">
                  </el-table-column>
                  <el-table-column prop="end_time" label="手动结束时间"></el-table-column>
                  <el-table-column label="操作">
                    <template slot-scope="scope">
                        <el-button type="danger" size="mini" @click="stopStream(scope.row)">结束推流</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                </div>  
                <script>  
                var Main = {
                    data() {
                      return {
                        formInline: {
                          file: '',
                          key: '',
                          times: 1,
                          duration: ''
                        },
                        rules: {
                          file: [{ required: true, message: '请输入推流文件', trigger: 'blur' }],
                          key: [{ required: true, message: '请输入推流密钥', trigger: 'blur' }]
                        },
                        streamTasks: []
                      }
                    },
                    created() {
                      axios.get('/tasks')
                      .then(response => {
                        this.streamTasks = response.data;
                      })
                      .catch(error => {
                        console.error(error);
                      });
                    },
                    methods: {
                      selectFile() {
                              this.$refs.fileInput.click();
                            },
                      handleFile() {
                              const file = this.$refs.fileInput.files[0];
                              console.log(file.path);
                              Vue.set(this.formInline, 'file', file.name);
                     },
                      openFullScreen1() {
                        const form = this.$refs.formInline
                        this.$refs.formInline.validate((valid) => {
                          if (valid) {
                              // 发送POST请求
                              axios.post('/stream', {
                                file: this.formInline.file,
                                key: this.formInline.key,
                                times: Number(this.formInline.times),
                                action:'start'
                                
                              })
                              .then(response => {
                                // 处理响应数据
                                console.log(response.data.duration);
                                console.log(Date.now() + 1000 * 60 * 60 * 8);
                                // 弹窗展示数据
                                this.$alert(response.data, '开始推流中，进程id：', {
                                  confirmButtonText: '确定',
                                  dangerouslyUseHTMLString: true
                                });
                                // 添加推流任务到列表
                                var task = {
                                  file: this.formInline.file,
                                  pid: response.data.pid,
                                  times: Number(this.formInline.times),
                                  duration: response.data.duration,
                                  start_time: Date.now(),
                                  status: "正在推流中"
                                }
                                this.streamTasks.push(task);
                              })
                              .catch(error => {
                                // 处理错误
                                console.error(error);
                              });
                        }
                        else {
                                    // 表单验证失败，提示错误信息
                                    this.$message.warning('回放视频和推流秘钥不能为空')
                                }
                      })   
                      },
                      stopStream(row){
                        // 发送POST请求
                        axios.post('/stream', {
                          pid: row.pid,
                          action: 'stop'
                        })
                        .then(response => {
                          // 处理响应数据
                          console.log(response.data);
                          // 更新推流任务状态
                          row.status = "推流已结束";
                          row.end_time = new Date().toLocaleString();
                        })
                        .catch(error => {
                          // 处理错误
                          console.error(error);
                        });
                      }
                    }                      
                }

                var Ctor = Vue.extend(Main)
                new Ctor().$mount('#app')    
                </script>       
                <hr/>
            </body>
        </html>
    '''

@app.route('/stream', methods=['POST'])
def stream():
    # 用于存储推流任务的列表
    try:
        # 从task.txt读取推流任务列表，并返回给前端
        with open("tasks.txt", "r") as f:
            stream_tasks = json.load(f)
    except Exception as e:
        stream_tasks = []
    action=request.get_json()['action']
    duration="未知"
    if action == 'start':
        file=request.get_json()['file']
        key=request.get_json()['key']
        times=request.get_json()['times']
        # 共享盘的路径
        shared_folder = r"\\192.168.0.202\共享盘"
        # 遍历共享盘及其子目录
        for dirpath, dirnames, filenames in os.walk(shared_folder):
            if file in filenames:
                # 找到了文件，输出完整路径
                file=os.path.join(dirpath, file)
                # 调用FFmpeg获取视频元数据信息
                result = subprocess.Popen(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = result.communicate()[0]
                # 解析输出中的时长信息
                duration = int(float(output.decode('utf-8').split('duration": "')[1].split('",')[0])*times*1000)
                break
        #推流的重复次数，在播放的次数的基础上-1就是重复的次数
        times=str(times-1)
        print(times)
        logs=key[0:22]+".txt"
        file=file.replace("\\","\\")
        #添加推流任务
        process = subprocess.Popen(['ffmpeg', '-re', '-stream_loop', times, '-i', file, '-c', 'copy', '-progress', logs, '-f', 'flv', 'rtmp://live-push.live.com/live/' + key], creationflags=subprocess.CREATE_NEW_CONSOLE)
        # 获取进程ID
        pid = process.pid
        print("子进程的进程ID为：", pid)
        # 将推流任务添加到列表
        task = {
            'file': request.get_json()['file'],
            'key': key,
            'times': int(times)+1,
            'pid': pid,
            'logs': logs,
            'status': '正在推流中',
            'duration': duration,
            'start_time': int(datetime.datetime.now().timestamp() * 1000),
            'end_time': ''
        }
        stream_tasks.append(task)
        save_tasks(stream_tasks)
        return {"pid": str(pid), "duration": duration}
    elif action == 'stop':
        pid=request.get_json()['pid']
        for task in stream_tasks:
            if task['pid'] == pid:
                pid = task['pid']
                # 结束推流进程
                os.system("taskkill /F /PID " + str(pid))
                # 更新推流任务状态
                task['status'] = "推流已结束"
                task['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_tasks(stream_tasks)
                return "推流任务已结束"
        return "找不到该推流任务"

@app.route('/tasks')
def get_tasks():
    # 从task.txt读取推流任务列表，并返回给前端
    if not os.path.isfile("tasks.txt"):
        with open("tasks.txt", "w") as f:
            pass
    try:
        # 从task.txt读取推流任务列表，并返回给前端
        with open("tasks.txt", "r+") as f:
            stream_tasks = json.load(f)
            for task in stream_tasks:
                process_exists = psutil.pid_exists(task['pid'])
                if process_exists:
                    print("进程存在")
                else:
                    print("进程不存在")
                    stream_tasks.remove(task)
                    save_tasks(stream_tasks)
    except Exception as e:
        stream_tasks = []

    return json.dumps(stream_tasks)

def save_tasks(stream_tasks):
    print(stream_tasks)
    with open("tasks.txt", "w") as f:
        json.dump(stream_tasks, f)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
