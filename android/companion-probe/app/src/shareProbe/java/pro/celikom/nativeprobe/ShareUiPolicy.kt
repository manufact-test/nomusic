package pro.celikom.nativeprobe

internal object ShareUiPolicy {
    data class Control(val packageName: String?, val id: String?, val text: String?, val description: String?, val visible: Boolean, val enabled: Boolean, val insidePlayer: Boolean)
    fun choose(controls: List<Control>, step: Int): Int? {
        val matches = controls.indices.filter { i ->
            val c=controls[i]
            c.packageName == "ru.yandex.music" && c.visible && c.enabled && when(step) {
                0 -> c.id == "ru.yandex.music:id/overflow_menu" && c.insidePlayer
                1 -> c.text?.trim() == "Поделиться"
                2 -> c.text?.trim() == "Ещё" || c.description?.trim() == "Ещё"
                else -> false
            }
        }
        return matches.singleOrNull()
    }
}
