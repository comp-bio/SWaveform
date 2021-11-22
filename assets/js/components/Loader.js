import axios from 'axios/index';

class Loader {
  constructor(parent) {
    this.parent = parent;
    this.cancel = {};
  }

  get(path, after) {
    if (this.cancel[path]) {
      this.cancel[path].cancel('Request canceled by user');
    }

    const CancelToken = axios.CancelToken;
    this.cancel[path] = CancelToken.source();

    const l = `loading:${path}`;
    this.parent.setState({[l]: true, ['data:' + path]: []});

    let data = {};
    if (this.parent.state && this.parent.state.chr) {
      data = {
        'chr': this.parent.state.chr,
        'start': this.parent.state.start,
        'end': this.parent.state.end,
        'types': this.parent.state.types,
        'datasets': this.parent.state.datasets,
      };
    }

    const obj = {
      url: `/api/${path}`,
      method: 'post',
      data:data,
      cancelToken: this.cancel[path].token
    };

    axios(obj)
      .then((res) => {
        this.parent.setState({['data:' + path]: res.data, [l]: false}, after);
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

export default Loader;
