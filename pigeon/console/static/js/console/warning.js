const Warning = {
  name: 'Warning',
  delimiters: ["[[", "]]"],
  props: [
    "show_modal",
    "warning",
    "warning_type"
  ],

  methods: {

    modal_ok() {
      this.$emit('modal_ok')
    },

    modal_cancel() {
      this.$emit('modal_cancel')
    }
  },

  template:`
    <div>
      <b-modal v-model="show_modal" hide-footer hide-header no-close-on-backdrop>
        <div class="d-block text-center">
          <h3>[[ warning.content ]]</h3>
        </div>
        <div class="space_around_style">
          <b-button
            class="mt-3"
            variant="outline-danger"
            @click="modal_ok"
          >
            [[ warning.ok_content ]]
          </b-button>
          <b-button
            class="mt-3"
            variant="outline-warning"
            @click="modal_cancel"
          >
            [[ warning.cancel_content ]]
          </b-button>
        </div>
      </b-modal>
    </div>
  `
};