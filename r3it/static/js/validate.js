function validateField(field, messages, invalidFeedback) {
    field = typeof field == "string" ? document.getElementById(field) : field
    const feedback = document.querySelector(invalidFeedback) || document.querySelector(`#${field.id}~.invalid-feedback`)

    function setFeedback() {
        field.setCustomValidity("")
        const messageNeeded = (state) => messages[state] && field.validity[state]

        if (messageNeeded("valueMissing")) {
            field.setCustomValidity(messages.valueMissing)
        } else if (messageNeeded("typeMismatch")) {
            field.setCustomValidity(messages.typeMismatch)
        } else if (messageNeeded("patternMismatch")) {
            field.setCustomValidity(messages.patternMismatch)
        } else if (messageNeeded("rangeUnderflow")) {
            field.setCustomValidity(messages.rangeUnderflow)
        } else if (messageNeeded("rangeOverflow")) {
            field.setCustomValidity(messages.rangeOverflow)
        } else if (messageNeeded("tooShort")) {
            field.setCustomValidity(messages.tooShort)
        } else if (messageNeeded("tooLong")) {
            field.setCustomValidity(messages.tooLong)
        } else if (messageNeeded("stepMismatch")) {
            field.setCustomValidity(messages.stepMismatch)
        } else if (messageNeeded("badInput")) {
            field.setCustomValidity(messages.badInput)
        }

        feedback.textContent = field.validationMessage
        if (invalidFeedback && field.validationMessage) {
            feedback.classList.add("show-feedback")
        } else {
            feedback.classList.remove("show-feedback")
        }
    }

    setFeedback()
    field.addEventListener("input", (evt) => {
        setFeedback()
    })
}

const validatePhone = (tel, messages) => validateField(tel, {
    valueMissing: "Phone number is required", 
    patternMismatch: "Phone number must be 10 digits",
    ...messages
})

const validateEmail = (email, messages) => validateField(email, {
    valueMissing: "Email address is required",
    typeMismatch: "Must be a valid email address",
    ...messages
})

const validateDate = (date, messages) => {
    date = typeof date == "string" ? document.getElementById(date) : date
    const [min, max] = [date.min, date.max]
    validateField(date, {
        valueMissing: messages.valueMissing || "Date is required",
        rangeUnderflow: messages.rangeUnderflow || `Date must be ${min.slice(5,7)}/${min.slice(8)}/${min.slice(0,4)} or later`,
        rangeOverflow: messages.rangeOverflow || `Date must be ${max.slice(5,7)}/${max.slice(8)}/${max.slice(0,4)} or earlier`,
        ...messages
    })
}

function validateAddress(fieldset) {
    const fields = fieldset.querySelectorAll("input[type='text'],select")
    const message = fieldset.querySelector("div.invalid-feedback")
    
    function setMessage() {
        let validationMessage = Array.prototype.map.call(fields, (field) => field.validationMessage).join("") // fallback for unexpected validation errors
        const missingFields = Array.prototype.filter.call(fields, (field) => field.validity.valueMissing)
        const disabled = Array.prototype.some.call(fields, (field) => field.disabled)

        if (missingFields.length > 0) {
            validationMessage = missingFields.reduce((prev, curr, i, array) => {
                const label = curr.getAttribute("aria-label")
                switch(i) {
                    case 0:
                        return label[0].toUpperCase() + label.slice(1) + 
                            (array.length == 1 ? " is required" : "")
                    case (array.length - 1):
                        return prev + " and " + label + " are required"
                    default:
                        return prev + ", " + label
                }
            }, "")
        } else if (fields[4].validity.patternMismatch) {
            validationMessage = "Zip code must be 5 digits"
        }

        message.textContent = validationMessage
        if (validationMessage && !disabled) {
            message.classList.add("show-feedback")
        } else {
            message.classList.remove("show-feedback")
        }
    }

    setMessage()
    fields.forEach((field) => {
        field.addEventListener("input", (evt) => {
            setMessage()
        })
    })
}