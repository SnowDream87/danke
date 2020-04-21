const regLogin = new Vue({
    el: '#registerForm',
    data:{
        userid:null,
        token:null,
        form: {
            username: null,
            realname: null,
            email: null,
            sex: null,
        },
    },
    created(){
        let token = $.cookie('token')
        this.token = token
        if (token) {
            let sex = {
                'true': 1,
                'false': 0
            }
            let useInfos = token.split('.')[1];
            let data = JSON.parse(window.atob(useInfos));
            this.userid = data.data.userid;
            fetch('/api/users/' + this.userid, {
                    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                })
                .then(resp => resp.json())
                .then(json => {
                    this.form.username = json.results[0].username;
                    this.form.realname = json.results[0].realname;
                    this.form.email = json.results[0].email;
                    this.form.sex = sex[json.results[0].sex]
                })
                
        }
    },
    methods:{
        onUpdate(){
            let formData = JSON.stringify(this.form);
            fetch("/api/users/" + this.userid + '/', {
                method:"PUT",
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token': this.token},
                body: formData
            }).then(resp => resp.json()).then(json => {
                if (json.code == 2000){
                    this.clearCookie()
                    location.href = '/rent/login/'
                }
                else {
                    alert(json.message)
                }
            });
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