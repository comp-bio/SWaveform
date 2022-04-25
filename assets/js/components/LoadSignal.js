import axios from 'axios/index';

class LoadSignal {
    constructor(parent) {
        this.parent = parent;
        this.cancel = null;
        this.page = 0;
    }

    get(append = false) {
        if (this.cancel) this.cancel.cancel('Request canceled by user');

        const CancelToken = axios.CancelToken;
        this.cancel = CancelToken.source();

        const l = `loading:signal`;
        this.parent.setState({[l]: true});

        if (append) {
            this.page += 1;
        } else {
            this.page = 0;
            this.parent.setState({'data:signal': [], 'more': true});
        }

        axios({
            url: `/api/signal`,
            method: 'post',
            data: {
                'chr': this.parent.state.chr,
                'start': this.parent.state.start,
                'end': this.parent.state.end,
                'types': this.parent.state.types,
                'side': this.parent.state.side,
                'dataset': this.parent.state.dataset,
                'population': this.parent.state.population,
                'page': this.page,
            },
            cancelToken: this.cancel.token
        })
            .then((res) => {
                this.parent.setState(prevState => {
                    prevState['data:signal'] = [...(append ? prevState['data:signal'] : []), ...res.data];
                    prevState[l] = false;
                    prevState['more'] = res.data.length === 24;
                    return prevState;
                });
            })
            .catch((thrown) => {
                if (axios.isCancel(thrown)) {
                    console.log('[STOP]', thrown.message);
                } else {
                    console.log('[ERROR]', thrown.message);
                    this.parent.setState({[l]: false});
                }
            });
    }
}

export default LoadSignal;
