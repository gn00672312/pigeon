const deepClone = function (obj) {

  function deepCloneArray (obj) {
    let _result = []
    for (let idx = 0; idx < obj.length; idx++) {
      let _clonedValue = obj[idx]
      if (Array.isArray(_clonedValue)) {
        _clonedValue = deepCloneArray(obj[idx])
      } else if (typeof _clonedValue === 'object') {
        _clonedValue = deepClone(obj[idx])
      }
      _result.push(_clonedValue)
    }
    return _result
  }

  let result = null
  if (Array.isArray(obj)) {
    result = []
  } else if (obj === null) {
    return null
  } else {
    result = {}
  }

  for (let propName in obj) {
    if (!obj.hasOwnProperty(propName)) { continue }
    let clonedValue = obj[propName]
    if (Array.isArray(clonedValue)) {
      clonedValue = deepCloneArray(obj[propName])
    } else if (typeof clonedValue === 'object') {
      clonedValue = deepClone(obj[propName])
    }
    result[propName] = clonedValue
  }
  return result
}


const FarmingEditor = {
  name: 'FarmingEditor',
  delimiters: ["[[", "]]"],
  components: {
    'warning': Warning,
  },

  props: [
    "activity_info",
    "edit_activity_name"
  ],

  data() {
    return {
      activity_name: "",
      activity_options: [],
      opened_options: [],
      selected_option_id: null,

      warning: {},
      warning_type: '',
      show_modal: false,
      show_editor: true
    }
  },

  created() {
    if (this.activity_info.hasOwnProperty('activity') && this.activity_info.hasOwnProperty('options')) {
      this.activity_name = this.activity_info.activity

      let options = deepClone(this.activity_info.options)
      options.forEach((option, idx) => {
        option.id = idx
        if (Array.isArray(option.content)) {
          option.content = option.content.join(";")
        }
      })

      this.activity_options.push(...options)
    }

    this.default_opened_options()
  },

  methods: {
    // draggable套件
    collapseComponentData() {
      return {
        on: {
          input: this.inputChanged
        },
        props: {
          value: this.opened_options
        }
      }
    },

    inputChanged(id) {
      this.opened_options = id;
    },

    add_option() {
      let new_option_id = this.activity_options.length

      this.activity_options.push({
        id: new_option_id,
        name: "",
        title: "",
        type: "single-option",
        content: []
      })
      this.opened_options.push(new_option_id)
    },

    cancel_modal() {
      this.cancel_activity()
    },

    delete_option(id) {
      this.selected_option_id = id
      this.delete_activity_option()
    },

    check_option(option) {
      if (option.name.length === 0) {
        return false
      }
      if (option.title.length === 0) {
        return false
      }
      if (option.content.length === 0) {
        return false
      }

      if (option.type === 'input') {
        if (!option.hasOwnProperty('unit')){
          return false
        }
      }

      return true
    },

    save_activity() {
      let to_save_data = true
      if (this.activity_name === '') {
        to_save_data = false
      }

      let options = [...this.activity_options]

      options.forEach(option => {
        if (!this.check_option(option)) {
          to_save_data = false
        }
      })

      if (to_save_data) {
        options.forEach(option => {
          delete option.id
          if (option.type !== 'input') {
            // 避免切換到 input 又切回來其他 option 時會增加 unit 欄位
            delete option.unit
            option.content = option.content.split(";")
          }
        })

        let save_activity_info = {"activity": this.activity_name, "options": options}
        this.$emit("save_activity", save_activity_info, this.edit_activity_name)
      }
      else {
        alert('資料欄位不得為空')
      }
    },

    delete_activity_option() {
      this.show_modal = true,
      this.warning = {
        content: "確定刪除這個項目嗎？",
        ok_content: "好，確定刪除",
        cancel_content: "不，取消刪除"
      },
      this.warning_type = 'delete_activity_option'
    },

    cancel_activity() {
      this.show_modal = true
      this.warning = {
        content: "確定取消這次編輯嗎？",
        ok_content: "好，確定取消",
        cancel_content: "不，繼續編輯"
      }
      this.warning_type = 'cancel_editing_activity'
    },

    modal_ok() {
      this.show_modal = false
      if (this.warning_type === 'delete_activity_option') {
        let delete_idx = this.activity_options.map(option => option.id).indexOf(this.selected_option_id)
        this.activity_options.splice(delete_idx, 1)
        let delete_open_id = this.opened_options.indexOf(this.selected_option_id)
        this.opened_options.splice(delete_open_id, 1)
        this.selected_option_id = null

      } else if (this.warning_type === 'cancel_editing_activity') {
        this.edit_activity_name = ''

        this.$emit("cancel_editing_activity")
      }
    },

    modal_cancel() {
      this.show_modal = false
    },

    default_opened_options() {
      if (this.activity_options) {
        this.opened_options = this.activity_options.map(option => option.id)
      } else {
        this.opened_options = []
      }
    }
  },

  template: `
    <div class="editor_container">
      <div>農務：
        <input v-model="activity_name">
      </div>
      <button
        class="add_btn add_style btn_style"
        @click="add_option"
      >
        新增項目
      </button>
      <draggable
        tag="el-collapse"
        :list="activity_options"
        :component-data="collapseComponentData()"
      >
        <el-collapse-item
          v-for="(option, idx) in activity_options"
          :key="idx"
          :name="option.id"
          :title="'項目： ' + option.name"
        >
          <div>
            <div>項目：
              <input v-model="option.name">
            </div>
            <div>標題：
              <input v-model="option.title">
            </div>
            <div>類型：
              <input
                id="radio_single"
                type="radio"
                value="single-option"
                v-model="option.type"
              >
                <label
                  for="radio_single"
                >
                  &nbsp;單選&emsp;
                </label>

              <input
                id="radio_multi"
                type="radio"
                value="multi-option"
                v-model="option.type"
              >
                <label
                  for="radio_multi"
                >
                  &nbsp;多選&emsp;
                </label>

              <input
                id="radio_input"
                type="radio"
                value="input"
                v-model="option.type"
              >
                <label
                  for="radio_input"
                >
                  &nbsp;輸入框
                </label>
            </div>

            <div
              v-if="option.type!=='input'"
            >選項(請用；分隔)：
              <textarea
                v-model="option.content"
              >
              </textarea>
            </div>

            <div v-else>
              <div>單位：<input v-model="option.unit"></div>
              <div>提示：<input v-model="option.content"></div>
            </div>
            <div>
              <button
                class="delete_btn delete_style btn_style"
                @click="delete_option(option.id)"
              >
                刪&emsp;除
              </button>
            </div>
          </div>
        </el-collapse-item>
      </draggable>

      <div class="space_around_style">
        <button
          class="edit_and_save_style btn_style"
          @click="save_activity"
        >
          儲&emsp;存
        </button>
        <button
          class="cancel_btn btn_style"
          @click="cancel_modal"
        >
          取&emsp;消
        </button>
      </div>

      <warning
        :show_modal="show_modal"
        :warning="warning"
        :warning_type="warning_type"
        @modal_ok="modal_ok"
        @modal_cancel="modal_cancel"
      ></warning>


    </div>
  `
};
