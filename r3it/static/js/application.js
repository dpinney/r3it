function setupForm() {
    function setupAltContact() {
        const useAltContact = document.getElementById("useAltContact")
        const altContact = document.getElementById("altContact")
        const requiredNames = ["name", "address", "city", "state", "zip", "email", "primaryPhone"]
        const fieldNames = ["name", "address", "address2", "city", "state", "zip", "email", "primaryPhone", "secondaryPhone", "fax"]
        const fields = fieldNames.map((field) => document.getElementById(`${field}AltContact`))
    
        function linkAltContact() {
            altContact.removeAttribute("hidden")
            requiredNames.forEach((field) => {
                document.getElementById(`${field}AltContact`).classList.add("required")
            })
        }
    
        function unlinkAltContact() {
            altContact.setAttribute("hidden", "true")
            requiredNames.forEach((field) => {
                document.getElementById(`${field}AltContact`).classList.remove("required")
            })
        }
    
        // initial link after check
        if (fields.some((field) => field.value != "")) {
            useAltContact.setAttribute("checked", "true")
            linkAltContact()
        }
    
        // event listener on checkbox
        useAltContact.addEventListener("click", () => {
            if (useAltContact.checked) {
                linkAltContact()
            } else {
                unlinkAltContact()
            }
        })
    }

    function setupMemberIsSelfContractor() {
        const memberIsSelfContractor = document.getElementById("memberIsSelfContractor")
        const memberIsSelfElectrician = document.getElementById("memberIsSelfElectrician")
        const contractorIsElectrician = document.getElementById("contractorIsElectrician")
        const nameContractor = document.getElementById('nameContractor')
    
        const fields = ["name", "address", "address2", "city", "state", "zip", "primaryPhone", "secondaryPhone", "email", "fax"]
        const fieldPairs = fields.map((field) => [document.getElementById(`${field}Contractor`), document.getElementById(`${field}Member`)])
        fieldPairs[0] = [document.getElementById('contactContractor'), fieldPairs[0][1]]
        const inputHandlers = fieldPairs.map((pair) => () => pair[0].value = pair[1].value)
    
        function linkMemberIsSelfContractor() {
            // for each contractor field, set val to member val
            nameContractor.value = ""
            fieldPairs.forEach((pair, i) => inputHandlers[i]())
            // for each member field, add evt list to set contractor val to member val
            fieldPairs.forEach((pair, i) => pair[1].addEventListener("input", inputHandlers[i]))
            // for each contractor field, set disabled
            nameContractor.setAttribute("disabled", "true")
            fieldPairs.forEach((pair) => pair[0].setAttribute("disabled", "true"))
            // disable contractorIsElectrician checkbox
            contractorIsElectrician.setAttribute("disabled", "true")
        }
    
        function unlinkMemberIsSelfContractor() {
            // for each member field, remove evt list
            fieldPairs.forEach((pair, i) => pair[1].removeEventListener("input", inputHandlers[i]))
            // for each contractor field, set empty
            fieldPairs.forEach((pair) => pair[0].value = "")
            // for each contractor field, remove disabled
            nameContractor.removeAttribute("disabled")
            fieldPairs.forEach((pair) => pair[0].removeAttribute("disabled"))
            // enable contractorIsElectrician checkbox
            if (!memberIsSelfElectrician.checked) {
                contractorIsElectrician.removeAttribute("disabled")
            }
        }
    
        // initial link after check
        if (fieldPairs.every((pair) => pair[0].value == pair[1].value)) {
            memberIsSelfContractor.setAttribute("checked", "true")
            linkMemberIsSelfContractor()
        }
    
        // event listener on checkbox
        memberIsSelfContractor.addEventListener("click", () => {
            if (memberIsSelfContractor.checked) {
                linkMemberIsSelfContractor()
            } else {
                unlinkMemberIsSelfContractor()
            }
        })
    }

    function setupMemberIsSelfElectrician() {
        const memberIsSelfContractor = document.getElementById("memberIsSelfContractor")
        const memberIsSelfElectrician = document.getElementById("memberIsSelfElectrician")
        const contractorIsElectrician = document.getElementById("contractorIsElectrician")
        const nameElectrician = document.getElementById('nameElectrician')
    
        const fields = ["name", "address", "address2", "city", "state", "zip", "primaryPhone", "secondaryPhone", "email", "fax"]
        const fieldPairs = fields.map((field) => [document.getElementById(`${field}Electrician`), document.getElementById(`${field}Member`)])
        fieldPairs[0] = [document.getElementById('contactElectrician'), fieldPairs[0][1]]
        const inputHandlers = fieldPairs.map((pair) => () => pair[0].value = pair[1].value)
    
        function linkMemberIsSelfElectrician() {
            // for each electrician field, set val to member val
            nameElectrician.value = ""
            fieldPairs.forEach((pair, i) => inputHandlers[i]())
            // for each member field, add evt list to set electrician val to member val
            fieldPairs.forEach((pair, i) => pair[1].addEventListener("input", inputHandlers[i]))
            // for each electrician field, set disabled
            nameElectrician.setAttribute("disabled", "true")
            fieldPairs.forEach((pair) => pair[0].setAttribute("disabled", "true"))
            // disable contractorIsElectrician checkbox
            contractorIsElectrician.setAttribute("disabled", "true")
        }
        
        function unlinkMemberIsSelfElectrician() {
            // for each member field, remove evt list
            fieldPairs.forEach((pair, i) => pair[1].removeEventListener("input", inputHandlers[i]))
            // for each electrician field, set empty
            fieldPairs.forEach((pair) => pair[0].value = "")
            // for each electrician field, remove disabled
            nameElectrician.removeAttribute("disabled")
            fieldPairs.forEach((pair) => pair[0].removeAttribute("disabled"))
            // enable contractorIsElectrician checkbox
            if (!memberIsSelfContractor.checked) {
                contractorIsElectrician.removeAttribute("disabled")
            }
        }
    
        // initial link after check
        if (fieldPairs.every((pair) => pair[0].value == pair[1].value)) {
            memberIsSelfElectrician.setAttribute("checked", "true")
            linkMemberIsSelfElectrician()
        }
    
        // event listener on checkbox
        memberIsSelfElectrician.addEventListener("click", () => {
            if (memberIsSelfElectrician.checked) {
                linkMemberIsSelfElectrician()
            } else {
                unlinkMemberIsSelfElectrician()
            }
        })
    }

    function setupContractorIsElectrician() {
        const memberIsSelfContractor = document.getElementById("memberIsSelfContractor")
        const memberIsSelfElectrician = document.getElementById("memberIsSelfElectrician")
        const contractorIsElectrician = document.getElementById("contractorIsElectrician")
    
        const fields = ["name", "contact", "address", "address2", "city", "state", "zip", "primaryPhone", "secondaryPhone", "email", "fax"]
        const fieldPairs = fields.map((field) => [document.getElementById(`${field}Electrician`), document.getElementById(`${field}Contractor`)])
        const inputHandlers = fieldPairs.map((pair) => () => pair[0].value = pair[1].value)
    
        function linkContractorIsElectrician() {
            // for each electrician field, set val to contractor val
            fieldPairs.forEach((pair, i) => inputHandlers[i]())
            // for each contractor field, add evt list to set electrician val to contractor val
            fieldPairs.forEach((pair, i) => pair[1].addEventListener("input", inputHandlers[i]))
            // for each electrician field, set disabled
            fieldPairs.forEach((pair) => pair[0].setAttribute("disabled", "true"))
            // disable memberIsSelfElectrician checkbox
            memberIsSelfContractor.setAttribute("disabled", "true")
            memberIsSelfElectrician.setAttribute("disabled", "true")
        }
    
        function unlinkContractorIsElectrician() {
            // for each contractor field, remove evt list
            fieldPairs.forEach((pair, i) => pair[1].removeEventListener("input", inputHandlers[i]))
            // for each electrician field, set empty
            fieldPairs.forEach((pair) => pair[0].value = "")
            // for each electrician field, remove disabled
            fieldPairs.forEach((pair) => pair[0].removeAttribute("disabled"))
            // enable memberIsSelfElectrician checkbox
            memberIsSelfContractor.removeAttribute("disabled")
            memberIsSelfElectrician.removeAttribute("disabled")
        }
        
        if (!memberIsSelfContractor.checked && 
            !memberIsSelfElectrician.checked && 
            fieldPairs.every((pair) => pair[0].value == pair[1].value)
        ) {
            contractorIsElectrician.setAttribute("checked", "true")
            linkContractorIsElectrician()
        }
    
        contractorIsElectrician.addEventListener("click", () => {
            if (contractorIsElectrician.checked) {
                linkContractorIsElectrician()
            } else {
                unlinkContractorIsElectrician()
            }
        })
    }

    function setupMemberIsOwner() {
        const memberIsOwner = document.getElementById("memberIsOwner")
        const nameMember = document.getElementById("nameMember")
        const owner = document.getElementById("owner")
        const handleMemberInput = () => owner.value = nameMember.value
    
        function linkMemberIsOwner() {
            handleMemberInput()
            nameMember.addEventListener("input", handleMemberInput)
            owner.setAttribute("disabled", "true")
        }
    
        function unlinkMemberIsOwner() {
            nameMember.removeEventListener("input", handleMemberInput)
            owner.value = ""
            owner.removeAttribute("disabled")
        }
    
        // initial link after check
        if (nameMember.value == owner.value) {
            memberIsOwner.setAttribute("checked", "true")
            linkMemberIsOwner()
        }
    
        // event listener on checkbox
        memberIsOwner.addEventListener("click", () => {
            if (memberIsOwner.checked) {
                linkMemberIsOwner()
            } else {
                unlinkMemberIsOwner()
            }
        })
    }
    
    function setupServiceAddrIsMemberAddr() {
        const serviceAddrIsMemberAddr = document.getElementById("serviceAddrIsMemberAddr")
        const fields = ["address", "address2", "city", "state", "zip"]
        // [[addressService, addressMember], [address2Service, addres2Member], [cityService, cityMember]...]
        const fieldPairs = fields.map((field) => [document.getElementById(`${field}Service`), document.getElementById(`${field}Member`)])
        const inputHandlers = fieldPairs.map((pair) => () => pair[0].value = pair[1].value)
    
        function linkServiceAddrIsMemberAddr() {
            fieldPairs.forEach((pair, i) => inputHandlers[i]())
            fieldPairs.forEach((pair, i) => pair[1].addEventListener("input", inputHandlers[i]))
            fieldPairs.forEach((pair) => pair[0].setAttribute("disabled", "true"))
        }
    
        function unlinkServiceAddrIsMemberAddr() {
            fieldPairs.forEach((pair, i) => pair[1].removeEventListener("input", inputHandlers[i]))
            fieldPairs.forEach((pair) => pair[0].value = "")
            fieldPairs.forEach((pair) => pair[0].removeAttribute("disabled"))
        }
    
        // initial link after check
        if (fieldPairs.every((pair) => pair[0].value == pair[1].value)) {
            serviceAddrIsMemberAddr.setAttribute("checked", "true")
            linkServiceAddrIsMemberAddr()
        }
    
        // event listener on checkbox
        serviceAddrIsMemberAddr.addEventListener("click", () => {
            if (serviceAddrIsMemberAddr.checked) {
                linkServiceAddrIsMemberAddr()
            } else {
                unlinkServiceAddrIsMemberAddr()
            }
        })
    }

    function setDatesMinToday() {
        const today = new Date()
        const [year, month, date] = [today.getFullYear(), today.getMonth() + 1, today.getDate()]
        const todayString = `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
        const dates = document.querySelectorAll("input[type='date']")
        Array.prototype.forEach.call(dates, (date) => date.setAttribute("min", todayString))
    }

    function linkInverterManufacturerModel() {
        const inverter = document.getElementById("inverter")
        const inverterManufacturer = document.getElementById("inverterManufacturer")
        const inverterModel = document.getElementById("inverterModel")
        const inverterOther = Array.from(document.getElementsByClassName("inverterOther"))
        
        // populates inverter field for saved inverter not in dropdown
        if ((inverterManufacturer.value || inverterModel.value) && inverter.selectedIndex == 0) {
            inverter.value = "Other"
            inverterOther.forEach((elem) => elem.removeAttribute("hidden"))
        }
        
        inverter.addEventListener("change", () => {
            const selected = inverter[inverter.selectedIndex]
            const optgroup = selected.parentNode.label
        
            if (selected.value == "Other") {
                inverterManufacturer.value = ""
                inverterModel.value = ""
                inverterOther.forEach((elem) => elem.removeAttribute("hidden"))
            } else {
                inverterManufacturer.value = optgroup
                inverterModel.value = selected.value
                inverterOther.forEach((elem) => elem.setAttribute("hidden", "true"))
            }
        })
    }

    function setupNetMeteringResetMonth() {
        const netMeteringRadio = document.getElementById("netMeteringRadio")
        const valueOfEnergyRadio = document.getElementById("valueOfEnergyRadio")
        const tariff = document.getElementById('dataTariff').dataset.tariff
        
        function createResetMonthRadio() {
            const netMeteringResetMonth = document.createElement("fieldset")
            netMeteringResetMonth.className = "col-6"
            netMeteringResetMonth.id = "netMeteringResetMonth"
            
            const legend = document.createElement("legend")
            legend.className = "col-form-label py-0"
            legend.textContent = "Net Metering kWh reset month"
            netMeteringResetMonth.appendChild(legend)
            
            const aprilGroup = document.createElement("div")
            aprilGroup.className = "form-check form-check-inline"
            const aprilInput = document.createElement("input")
            aprilInput.type = "radio"
            aprilInput.className = "form-check-input"
            aprilInput.id = "aprilRadio"
            aprilInput.name = "Reset month"
            aprilInput.value = "April kWh reset"
            aprilInput.setAttribute("required", "true")
            aprilGroup.appendChild(aprilInput)
            const aprilLabel = document.createElement("label")
            aprilLabel.htmlFor = "aprilRadio"
            aprilLabel.className = "form-check-label"
            aprilLabel.textContent = "April"
            aprilGroup.appendChild(aprilLabel)
            netMeteringResetMonth.appendChild(aprilGroup)
            
            const novemberGroup = document.createElement("div")
            novemberGroup.className = "form-check form-check-inline"
            const novemberInput = document.createElement("input")
            novemberInput.type = "radio"
            novemberInput.className = "form-check-input"
            novemberInput.id = "novemberRadio"
            novemberInput.name = "Reset month"
            novemberInput.value = "November kWh reset"
            novemberInput.setAttribute("required", "true")
            novemberGroup.appendChild(novemberInput)
            const novemberLabel = document.createElement("label")
            novemberLabel.htmlFor = "novemberRadio"
            novemberLabel.className = "form-check-label"
            novemberLabel.textContent = "November"
            novemberGroup.appendChild(novemberLabel)
            netMeteringResetMonth.appendChild(novemberGroup)
        
            const tariffType = document.getElementById("tariffType")
            tariffType.after(netMeteringResetMonth)
        }
        
        // initialize checked net metering, month if exists
        if (tariff.startsWith("Net metering")) {
            createResetMonthRadio()
            netMeteringRadio.setAttribute("checked", "true")
            if (tariff.includes("April")) {
                document.querySelector("#aprilRadio").setAttribute("checked", "true")
            } else if (tariff.includes("November")) {
                document.querySelector("#novemberRadio").setAttribute("checked", "true")
            } else {
                console.error(`Bad tariff string: ${tariff}`)
            }
        } else {
            valueOfEnergyRadio.setAttribute("checked", "true")
        }
    
        // event listeners on radios
        netMeteringRadio.addEventListener("click", () => {
            const netMeteringResetMonth = document.querySelector("#netMeteringResetMonth")
            if (!netMeteringResetMonth) {
                createResetMonthRadio()
            }
        })
        valueOfEnergyRadio.addEventListener("click", () => {
            const netMeteringResetMonth = document.querySelector("#netMeteringResetMonth")
            if (netMeteringResetMonth) {
                netMeteringResetMonth.remove()
            }
        })
    }

    function maskTels() {
        const tels = document.querySelectorAll("input[type='tel']")
        Array.prototype.forEach.call(tels, (tel) => {
            // NOTE: necessary here? why not place in elements?
            tel.placeholder = "(xxx) xxx - xxxx"
            VMasker(tel).maskPattern("(999) 999 - 9999")
        })
    }
    
    function maskZips() {
        const zips = document.querySelectorAll("[id^='zip']")
        Array.prototype.forEach.call(zips, (zip) => VMasker(zip).maskPattern("99999"))
    }

    function submitForm() {
        function showSpinner() {
            const submitSpinner = document.getElementById("submitSpinner")
            const submitButton = document.getElementById("submit")
            submitSpinner.removeAttribute("hidden")
            submitButton.childNodes[2].textContent = "Submitting Application..."
        }
    
        function unmaskTels() {
            const tels = document.querySelectorAll("input[type='tel']")
            Array.prototype.forEach.call(tels, (tel) => VMasker(tel).unMask())
        }
    
        function unmaskZips() {
            const zips = document.querySelectorAll("[id^='zip']")
            Array.prototype.forEach.call(zips, (zip) => VMasker(zip).unMask())
        }
    
        function cleanUpAltContact() {
            const useAltContact = document.getElementById("useAltContact")
            if (!useAltContact.checked) {
                const fields = ["name", "address", "address2", "city", "state", "zip", "primaryPhone", "secondaryPhone", "email", "fax"]
                const altContactFields = fields.map((field) => document.getElementById(`${field}AltContact`))
                document.querySelector("#stateAltContact > [value='']").removeAttribute("disabled") // different version of below line
                // altContactFields[4].childNodes[1].removeAttribute("disabled")   // required to actually save alt contact state empty string
                altContactFields.forEach((field) => field.value = "")
            }
        }
    
        function combineTariff() {
            const netMeteringRadio = document.getElementById("netMeteringRadio")
            if (netMeteringRadio.checked) {
                const aprilRadio = document.querySelector("#aprilRadio")
                const novemberRadio = document.querySelector("#novemberRadio")
                if (aprilRadio.checked) {
                    netMeteringRadio.value += " " + aprilRadio.value
                } else if (novemberRadio.checked) {
                    netMeteringRadio.value += " " + novemberRadio.value
                }
                const netMeteringResetMonth = document.querySelector("#netMeteringResetMonth")
                if (netMeteringResetMonth) {
                    netMeteringResetMonth.remove()
                }
            }
        }
    
        function combineInstallationType() {
            const installationType = document.querySelector("#installationType")
            const [selfCont, selfElec, contElec] = [memberIsSelfContractor.checked, memberIsSelfElectrician.checked, contractorIsElectrician.checked]
            installationType.value = (() => {
                switch (true) {
                    case !selfCont && !selfElec && !contElec:
                        return "Contractor and Electrician"
                    case !selfCont && !selfElec && contElec:
                        return "Contractor only"
                    case !selfCont && selfElec && !contElec:
                        return "Contractor and Self-electric"
                    case selfCont && !selfElec && !contElec:
                        return "Self-install and Electrician"
                    case selfCont && selfElec && !contElec:
                        return "Self-install and Self-electric"
                }
            })()
        }
        
        function enableCopiedFields() {
            const disabled = document.querySelectorAll(".form-control[disabled],.form-select[disabled]")
            Array.prototype.forEach.call(disabled, (field) => field.removeAttribute("disabled"))
        }
    
        showSpinner() // submit button spinner
        unmaskTels()
        unmaskZips()
        cleanUpAltContact() // sets alt contact fields to empty if not checked
        combineTariff() // combines tariff and month radio buttons
        combineInstallationType() // combines checkboxes into installation type
        enableCopiedFields() // remove disabled from copied fields so they submit
    }

    setupAltContact()
    setupMemberIsSelfContractor()
    setupMemberIsSelfElectrician()
    setupContractorIsElectrician()
    setupMemberIsOwner()
    setupServiceAddrIsMemberAddr()
    setDatesMinToday()
    linkInverterManufacturerModel()
    setupNetMeteringResetMonth()
    maskTels()
    maskZips()

    const form = document.querySelector(".needs-validation")
    form.addEventListener("submit", (evt) => {
        if (!form.checkValidity()) {
            evt.preventDefault()
            evt.stopPropagation()
        } else {
            submitForm()
        }
        form.classList.add("was-validated")
    }, false)
}

setupForm()
