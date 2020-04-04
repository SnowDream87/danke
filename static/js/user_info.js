const app = new Vue({
    el: '#app',
    data: {
        houseNext:{
            count: 0,
            nextPage: null,
            prevPage: null,
        },
        userNext:{
            count: 0,
            nextPage: null,
            prevPage: null,
        },
        url: '/api/users/',
        userId: null,
        user: [],
        roleId: null,
        houseInfos:[],
        users: [],
        blockHistory: false,
        blockUsers: false,
        userType: null,
        token: null,
        userDate: {
            name: null,
            tel: null,
            servstar: 0,
            realstar: 0,
            profstar: 0
        }
    },
    created(){
        let token = $.cookie('token')
        this.token = token
        if (token) {
            let houseInfos = token.split('.')[1];
            let data = JSON.parse(window.atob(houseInfos));
            this.userId = data.data.userid;
            this.roleId = data.data.roleid;
            let dictionary = {
                '1': '普通用户',
                '2': '经理人',
                '4': '管理员'
            };
            this.userType = dictionary[this.roleId];
            fetch(this.url + this.userId, {
                    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                }).then(resp => resp.json())
                    .then(json => {
                    this.user = json.results[0];
                    this.userDate.name = json.results[0].realname;
                    this.userDate.tel = json.results[0].tel;
                })
        }
        else {
            location.href = '/rent/login/'
        }
    },
    methods:{
        houseHandleCurrentChange(currentPage){
            this.houseLoadData('/api/houseinfos/?page=' + currentPage)
        },
        houseLoadData(url) {
            if (url) {
                fetch(url + '&user=' + this.userId)
                    .then(resp => resp.json())
                    .then(json => {
                        this.houseNext.count = json.count;
                        this.houseNext.nextPage = json.next;
                        this.houseNext.prevPage = json.previous;
                        this.houseInfos = json.results;
                    })
            }
        },
        userHandleCurrentChange(currentPage){
            this.userLoadData('/api/users/?page=' + currentPage)
        },
        userLoadData(url) {
            if (url) {
                fetch(url, {
                        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                    })
                    .then(resp => resp.json())
                    .then(json => {
                        this.houseNext.count = json.count;
                        this.houseNext.nextPage = json.next;
                        this.houseNext.prevPage = json.previous;
                        this.houseInfos = json.results;
                    })
            }
        },
        history(){
            this.blockHistory = !this.blockHistory;
            fetch('/api/houseinfos/' + '?user=' + this.userId)
                .then(resp => resp.json())
                .then(json => {
                    this.houseInfos = json.results;
                    this.houseNext.count = json.count;
                    this.houseNext.nextPage = json.next;
                    this.houseNext.prevPage = json.previous;
                });
        },
        historyDeleted(e){
            let el = e.currentTarget.parentElement.parentElement.parentElement.firstChild.firstChild.textContent;
            let url = '/api/houseinfos/';
            this.selectData(el, url);
            this.sleep(500);
            this.refreshHouseInfoData(url);
        },
        userDeleted(e){
            let el = e.currentTarget.parentElement.parentElement.parentElement.firstChild.firstChild.textContent;
            let url = '/api/users/';
            this.selectData(el, url);
            this.refreshUserData(url);
        },
        seeUsers(){
            this.blockUsers = !this.blockUsers;
            fetch('/api/users/',  {
                        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                })
                .then(resp => resp.json())
                .then(json => {
                    this.users = json.results;
                    this.userNext.count = json.count;
                    this.userNext.nextPage = json.next;
                    this.userNext.prevPage = json.previous;
                })
        },
        registerAgent(){
            let agentData = JSON.stringify(this.userDate);
            console.log(agentData);
            let data = JSON.stringify({"role_user": true});
            fetch('/api/agents/', {
                method: 'POST',
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json'},
                body: agentData,
            }).then(resp => resp.json()).then();
            fetch('/api/users/' + this.userId + '/', {
                method: 'PUT',
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                body: data,
            }).then(resp => resp.json()).then(json => {
                this.setCookie(-1);
                alert(json.message + '请重新登录');
                location.href = '/rent/login/'
            })
        },
        userRefresh(){
            let url = '/api/users/';
            this.refreshUserData(url);
        },
        houseRefresh(){
            let url = '/api/houseinfos/';
            this.refreshHouseInfoData(url);
        },
        selectData(el, url){
            fetch(url + el + '/', {method: 'PUT'})
                .then(resp => resp.json())
                .then(json => alert(json.message))
        },
        refreshUserData(url){
            fetch(url,  {
                        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'token':this.token},
                })
                .then(resp => resp.json())
                .then(json => this.users = json.results)
        },
        refreshHouseInfoData(url){
            if (this.userId){
                fetch(url + '?user=' + this.userId)
                    .then(resp => resp.json())
                    .then(json => {
                        this.houseInfos = json.results;
                        this.houseNext.count = json.count;
                    })
            }
        },
        sleep(d){
            for(let t = Date.now();Date.now() - t <= d;);
        },
        setCookie(days){
            let token = $.cookie('token');
            let date = new Date();
            date.setTime(date.getTime()+(1000 * 86400 * days));
            let expires = "; expires="+date.toGMTString();
            document.cookie = "token=" + token + expires + "; path=/";
        },
    }
});
