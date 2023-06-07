from flask import Flask, request
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    # 返回 HTML 页面
    return '''
        <html>
            <head>
                <title>网页直播推流工具</title>
                <link rel="stylesheet" href="//unpkg.com/element-ui@2.15.13/lib/theme-chalk/index.css">
                
            </head>
            <body>
                <script src="//unpkg.com/vue@2/dist/vue.js"></script>
                <script src="//unpkg.com/element-ui@2.15.13/lib/index.js"></script>
                <script src="//unpkg.com/axios/dist/axios.min.js"></script>
                <div id="app">
                <h2>网页直播推流工具</h2>
                <el-form ref="formInline" :inline="true" :model="formInline"  :rules="rules" class="demo-form-inline">
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
                </div>  
                <script>  
                var Main = {
                    data() {
                      return {
                        formInline: {
                          file: '',
                          key: '',
                          times: 1
                        },
                        rules: {
                          file: [{ required: true, message: '请输入推流文件', trigger: 'blur' }],
                          key: [{ required: true, message: '请输入推流密钥', trigger: 'blur' }]
                        }                   
                      }
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
                                console.log(response.data);
                                // 弹窗展示数据
                                this.$alert(response.data, '开始推流', {
                                  confirmButtonText: '确定',
                                  dangerouslyUseHTMLString: true
                                })
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
    print(request)
    action=request.get_json()['action']
    print(action)
    if action == 'start':
        file=request.get_json()['file']
        # 需要推流的本地视频路径
        shared_folder = r"\\192.168.1.1\共享盘"
        # 遍历共享盘及其子目录。如果是m3u8地址则不会跑下面的for循环内容
        for dirpath, dirnames, filenames in os.walk(shared_folder):
            if file in filenames:
                # 找到了文件，输出完整路径
                file=os.path.join(dirpath, file)
                break
        key=request.get_json()['key']
        times=request.get_json()['times']-1
        times=str(times)
        logs=key[0:22]+".txt"
        file=file.replace("\\","\\")
        print(file,key,times,logs)
        subprocess.Popen(['ffmpeg', '-re', '-stream_loop', times, '-i', file, '-c', 'copy', '-progress', logs, '-f', 'flv', 'rtmp://push.******.com/' + key], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return '''
                <html>
                    <head>
                        <title>日志查看</title>
                    </head>
                    <body>
                        <p>日志文件</p>
                        <a href="/show_logs?log_id=%s">查看日志</a>
                    </body>
                </html>
            ''' % (logs)
def get_logs(logs_file):
    lines=50
    with open(logs_file, 'r') as f:
        try:
            f.seek(-1024, 2) #先定位到文件的倒数1024个字节处，避免读取整个文件
        except IOError:
            f.seek(0)
        lines_str = f.read().splitlines()
    if len(lines_str) >= lines:
        return lines_str[-lines:]
    else:
        return lines_str
@app.route('/show_logs')
def show_logs():
    logs_file = request.args.get('log_id')
    print(logs_file)
    logs = get_logs(logs_file)
    log_text = '\n'.join(logs)
    return '''
                <html>
                    <head>
                        <title>日志查看</title>
                        <meta http-equiv="refresh" content="10"> # 自动刷新页面 10s
                    </head>
                    <body>
                        <p>日志内容</p>
                        <pre>%s</pre> 
                    </body>
                </html>
            ''' % (log_text)
if __name__ == '__main__':
    app.run(port=80)
