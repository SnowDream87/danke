const regLogin = new Vue({
    el: '#registerForm',
    data:{
        againMessage: null,
        newMessage: null,
        message: null,
        userid: null,
        token: null,
        againPassword: null,
        form: {
            oldPassword: null,
            password: null,
        },
    },
    created(){
        let token = $.cookie('token')
        this.token = token
        if (token) {
            let useInfos = token.split('.')[1];
            let data = JSON.parse(window.atob(useInfos));
            this.userid = data.data.userid; 
        }
    },
    methods:{
        onUpdate(){
            this.message = null;
            this.newMessage = null;
            this.againMessage = null;
            let formData = JSON.stringify(this.form);
            if (this.form.password.length >= 6) {
                if (this.form.password == this.againPassword) {
                    fetch("/api/users/" + this.userid + '/', {
                        method:"PUT",
                        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token': this.token},
                        body: formData
                    }).then(resp => resp.json()).then(json => {
                        if (json.code == 2000) {
                            this.clearCookie()
                            location.href = '/rent/login/'  
                        }
                        else {
                            this.message = json.message
                        }
                        
                    });
                }
                else {
                    this.againMessage = "确认密码与新密码不一致"
                }
            }
            else {
                this.newMessage = "新密码长度应大于等于6位"
            }
            
        },
        setCookie(days){
                let token = $.cookie('token');
                let date = new Date();
                date.setTime(date.getTime()+(1000 * 86400 * days));
                let expires = "; expires="+date.toGMTString();
                document.cookie = "token=" + token + expires + "; path=/";
        },
        clearCookie(){
            this.setCookie(-1)
        },
    }
})