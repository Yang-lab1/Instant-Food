export function createStore(initialState) {
  let state = { ...initialState };

  return {
    getState() {
      return state;
    },
    setState(nextState) {
      state = { ...state, ...nextState };
      return state;
    }
  };
}
